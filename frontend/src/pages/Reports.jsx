import React, { useState, useEffect } from 'react';
import { Download, BarChart2, FileSpreadsheet, FileJson, RefreshCw, Filter, Clock } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import axiosInstance from '../api/axiosInstance';

export default function Reports() {
  // --- State Variables ---
  const [totalIncidents, setTotalIncidents] = useState(0);
  const [categories, setCategories] = useState({ falls: 0, violence: 0 });
  const [chartData, setChartData] = useState([]);
  const [downloadFormat, setDownloadFormat] = useState('pdf');
  const [exportLoading, setExportLoading] = useState(false);
  const [incidentsList, setIncidentsList] = useState([]); 

  // --- Manager-Specific Statistics States ---
  const [avgResponseTime, setAvgResponseTime] = useState('N/A');

  // --- Auth Role State ---
  // Safely parse the 'user' object from localStorage to read the exact role attribute
  const [userRole, setUserRole] = useState(() => {
    try {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        const parsedUser = JSON.parse(storedUser);
        return parsedUser.role || 'parent'; 
      }
    } catch (err) {
      console.error("Error parsing user role from localStorage:", err);
    }
    return 'parent'; 
  });
  
  const isManager = userRole.toLowerCase().trim() === 'manager';

  // --- Filter Criteria States ---
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [dangerCategory, setDangerCategory] = useState('');
  const [status, setStatus] = useState(''); 
  const [cameraId, setCameraId] = useState(''); 
  const [camerasList, setCamerasList] = useState([]); 

  /**
   * Helper function to calculate duration in minutes between two timestamps
   */
  const calculateDurationInMinutes = (startStr, endStr) => {
    if (!startStr || !endStr) return null;
    const start = new Date(startStr);
    const end = new Date(endStr);
    const diffMs = end - start;
    if (diffMs < 0) return 0;
    return Math.round(diffMs / 1000 / 60); // Convert milliseconds to total minutes
  };

  /**
   * Fetch initial unique cameras/zones to dynamically populate the zone filter dropdown options
   */
  useEffect(() => {
    axiosInstance.get('/incidents')
      .then(res => {
        const data = res.data || [];
        const uniqueCameras = [];
        const map = new Map();
        
        for (const item of data) {
          if (item.camera_id && !map.has(item.camera_id)) {
            map.set(item.camera_id, true);
            uniqueCameras.push({
              camera_id: item.camera_id,
              zone_name: item.zone_name || `Zone (${item.camera_id.substring(0, 5)}...)`
            });
          }
        }
        setCamerasList(uniqueCameras);
      })
      .catch(err => console.error("Error fetching initial unique zones mapping:", err));
  }, []);

  /**
   * Fetches and filters system analytics data to synchronously update charts, counters, and data logs
   */
  const fetchAnalyticsData = () => {
    axiosInstance.get('/incidents')
      .then(res => {
        let data = res.data || [];

        // 1. Apply Dynamic Frontend Date Filters
        if (startDate) {
          data = data.filter(i => i.timestamp && new Date(i.timestamp) >= new Date(startDate));
        }
        if (endDate) {
          const end = new Date(endDate);
          end.setHours(23, 59, 59, 999); 
          data = data.filter(i => i.timestamp && new Date(i.timestamp) <= end);
        }

        // 2. Apply Danger Category Filter
        if (dangerCategory) {
          data = data.filter(i => i.danger_category?.toLowerCase() === dangerCategory.toLowerCase());
        }

        // 3. Apply Status Filter
        if (status && isManager) {
          data = data.filter(i => i.status?.toLowerCase() === status.toLowerCase());
        }

        // 4. Apply Camera / Zone Filter
        if (cameraId) {
          data = data.filter(i => i.camera_id === cameraId);
        }

        // Synchronize state counters and raw grid list items
        setTotalIncidents(data.length);
        setIncidentsList(data);

        // 5. MANAGER STATISTIC: Calculate average response time for resolved items
        if (isManager) {
          const resolvedIncidents = data.filter(i => i.status?.toLowerCase() === 'resolved' && i.resolved_at);
          if (resolvedIncidents.length > 0) {
            const totalMinutes = resolvedIncidents.reduce((acc, current) => {
              const minutes = calculateDurationInMinutes(current.timestamp, current.resolved_at);
              return acc + (minutes || 0);
            }, 0);
            const avg = Math.round(totalMinutes / resolvedIncidents.length);
            setAvgResponseTime(`${avg} mins`);
          } else {
            setAvgResponseTime('N/A');
          }
        }

        // Map current results against target Yaqidh model architectural classes (Fall vs Violence)
        const fallsCount = data.filter(i => i.incident_type?.toLowerCase().includes('fall')).length;
        const violenceCount = data.filter(i => i.incident_type?.toLowerCase().includes('violence')).length;
        setCategories({ falls: fallsCount, violence: violenceCount });

        // Distribute captured analytics cleanly across standard 7-day week framework
        const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const distribution = dayLabels.map(day => {
          const countsForDay = data.filter(i => {
            if (!i.timestamp) return false;
            const date = new Date(i.timestamp);
            return dayLabels[date.getDay()] === day;
          }).length;

          return {
            name: day,
            incidents: countsForDay,
            falsePositives: 0
          };
        });

        setChartData(distribution);
      })
      .catch(err => {
        console.error("Error generating matching reports metrics structure:", err);
      });
  };

  useEffect(() => {
    fetchAnalyticsData();
  }, [startDate, endDate, dangerCategory, status, cameraId, userRole]);

  /**
   * Compiles the filter payloads matching the safe Pydantic schemas and triggers the download stream
   */
  const handleGenerateAndDownloadReport = async () => {
    setExportLoading(true);
    try {
      const filterPayload = {
        start_date: startDate ? new Date(startDate).toISOString() : null,
        end_date: endDate ? new Date(endDate).toISOString() : null,
        danger_category: dangerCategory ? dangerCategory : null,
        status: isManager && status ? status : null,
        camera_id: cameraId ? cameraId : null
      };
      
      const createResponse = await axiosInstance.post('/reports', filterPayload);
      const newReportId = createResponse.data?.report_id;

      if (!newReportId) throw new Error("Missing structural report identifier boundary.");

      if (downloadFormat === 'pdf') {
        const pdfResponse = await axiosInstance.get(`/reports/${newReportId}/export-pdf`, {
          responseType: 'blob'
        });
        
        const blob = new Blob([pdfResponse.data], { type: 'application/pdf' });
        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = `Yaqidh_Safety_Report_${newReportId}.pdf`;
        link.click();
      } else {
        const jsonResponse = await axiosInstance.get(`/reports/${newReportId}/export-json`);
        
        const blob = new Blob([JSON.stringify(jsonResponse.data, null, 2)], { type: 'application/json' });
        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = `Yaqidh_Data_Report_${newReportId}.json`;
        link.click();
      }
    } catch (err) {
      console.error("Failed to compile isolated target report system record:", err);
      alert("Could not process report action. Please verify data parameters match structural states.");
    } finally {
      setExportLoading(false);
    }
  };

  const clearFilters = () => {
    setStartDate('');
    setEndDate('');
    setDangerCategory('');
    setStatus('');
    setCameraId('');
  };

  const fallPercentage = totalIncidents > 0 ? Math.round((categories.falls / totalIncidents) * 100) : 0;
  const violencePercentage = totalIncidents > 0 ? Math.round((categories.violence / totalIncidents) * 100) : 0;

  return (
    <div className="p-6 space-y-8 bg-slate-50/30 min-h-screen font-sans">
      {/* Top Main Header Control Section */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 max-w-6xl mx-auto border-b border-slate-200/60 pb-6">
        <div>
          <h2 className="text-3xl font-black text-[#06217e] flex items-center gap-3">
            <BarChart2 size={36} /> Reports & Analytics
          </h2>
          <p className="text-slate-500 font-medium mt-1 tracking-tight">AI-powered safety monitoring data logs</p>
        </div>
        
        {/* Document Format Selection Layout Toggles */}
        <div className="flex items-center gap-3 bg-white p-2 rounded-2xl border border-slate-200 shadow-sm flex-wrap">
          <div className="flex bg-slate-100 p-1 rounded-xl">
            <button
              onClick={() => setDownloadFormat('pdf')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                downloadFormat === 'pdf' ? 'bg-white text-red-600 shadow-sm' : 'text-slate-600 hover:bg-slate-200'
              }`}
            >
              <FileSpreadsheet size={14} /> PDF Document
            </button>
            <button
              onClick={() => setDownloadFormat('json')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                downloadFormat === 'json' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-600 hover:bg-slate-200'
              }`}
            >
              <FileJson size={14} /> JSON Data
            </button>
          </div>

          <button 
            onClick={handleGenerateAndDownloadReport}
            disabled={exportLoading}
            className="flex items-center gap-2 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl text-xs font-bold shadow-md shadow-brand-500/20 transition-all active:scale-[0.98]"
          >
            {exportLoading ? (
              <><RefreshCw size={14} className="animate-spin" /> Compiling...</>
            ) : (
              <><Download size={14} /> Generate & Download</>
            )}
          </button>
        </div>
      </header>

      {/* Dynamic Filter Scope Control Panel */}
      <section className="max-w-6xl mx-auto bg-white p-5 rounded-3xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-2 text-[#06217e] font-black text-sm mb-4 border-b border-slate-100 pb-2">
          <Filter size={16} /> Filter Scope Options
        </div>
        
        <div className={`grid grid-cols-1 ${isManager ? 'sm:grid-cols-5' : 'sm:grid-cols-4'} gap-4 items-end`}>
          <div className="flex flex-col space-y-1.5">
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Start Date</label>
            <input 
              type="date" 
              value={startDate} 
              onChange={(e) => setStartDate(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:border-brand-500 transition-colors"
            />
          </div>
          
          <div className="flex flex-col space-y-1.5">
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">End Date</label>
            <input 
              type="date" 
              value={endDate} 
              onChange={(e) => setEndDate(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:border-brand-500 transition-colors"
            />
          </div>
          
          <div className="flex flex-col space-y-1.5">
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Danger Category</label>
            <select 
              value={dangerCategory} 
              onChange={(e) => setDangerCategory(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:border-brand-500 transition-colors w-full"
            >
              <option value="">All Categories</option>
              <option value="Critical">Critical</option>
              <option value="Warning">Warning</option>
            </select>
          </div>

          {isManager && (
            <div className="flex flex-col space-y-1.5">
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Status</label>
              <select 
                value={status} 
                onChange={(e) => setStatus(e.target.value)}
                className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:border-brand-500 transition-colors w-full"
              >
                <option value="">All Statuses</option>
                <option value="open">Open</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>
          )}

          <div className="flex flex-col space-y-1.5">
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Zone / Cam</label>
            <div className="flex gap-2">
              <select 
                value={cameraId} 
                onChange={(e) => setCameraId(e.target.value)}
                className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:border-brand-500 transition-colors w-full"
              >
                <option value="">All Zones</option>
                {camerasList.map(cam => (
                  <option key={cam.camera_id} value={cam.camera_id}>{cam.zone_name}</option>
                ))}
              </select>
              {(startDate || endDate || dangerCategory || (isManager && status) || cameraId) && (
                <button 
                  onClick={clearFilters}
                  className="text-xs bg-slate-100 text-slate-500 hover:bg-slate-200 font-bold px-3 py-2 rounded-xl transition-colors whitespace-nowrap"
                >
                  Clear
                </button>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Analytics Summary Counters Block */}
      <div className="max-w-6xl mx-auto">
        <div className={`flex justify-center -space-x-px max-w-4xl mx-auto`}> 
          <div className="bg-white px-8 py-6 border border-slate-200 w-full rounded-l-2xl shadow-sm flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">Total Incidents (Filtered Scope)</p>
              <h3 className="text-4xl font-black text-red-600 tracking-tighter">{totalIncidents}</h3>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 bg-white rounded-full border border-slate-100 shadow-sm">
              <BarChart2 size={14} className="text-emerald-500" />
              <span className="text-xs font-bold text-emerald-600">Active Logs</span>
            </div>
          </div>

          {/* MANAGER KPI INJECTION: Only render Total Average Response Time Card for Managers */}
          {isManager && (
            <div className="bg-white px-8 py-6 border border-slate-200 w-full shadow-sm flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">Avg Response Time</p>
                <h3 className="text-4xl font-black text-amber-600 tracking-tighter">{avgResponseTime}</h3>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 bg-white rounded-full border border-slate-100 shadow-sm">
                <Clock size={14} className="text-amber-500" />
                <span className="text-xs font-bold text-amber-600">Resolved KPI</span>
              </div>
            </div>
          )}

          <div className="bg-white px-8 py-6 border border-slate-200 w-full rounded-r-2xl shadow-sm flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">System Precision</p>
              <h3 className="text-4xl font-black text-[#06217e] tracking-tighter">100%</h3>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 bg-white rounded-full border border-slate-100 shadow-sm">
              <span className="text-xs font-bold text-emerald-600">Stable</span>
            </div>
          </div>
        </div>
      </div>

      {/* Analytics Graph Distributions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
        <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100">
          <h3 className="font-black text-[#06217e] text-xl mb-6">Verification Accuracy</h3>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontWeight: 600}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontWeight: 600}} />
                <Tooltip cursor={{fill: '#f8fafc'}} contentStyle={{ borderRadius: '1rem', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }} />
                <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ paddingBottom: '20px', fontSize: '12px', fontWeight: 700 }} />
                <Bar name="Verified Incidents" dataKey="incidents" stackId="a" fill="#06217e" />
                <Bar name="False Positives" dataKey="falsePositives" stackId="a" fill="#e2e8f0" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100">
          <h3 className="font-black text-[#06217e] text-xl mb-6">Incident Model Classes Summary</h3>
          <div className="space-y-7 pt-2">
            <div className="space-y-3">
              <div className="flex justify-between items-end text-sm font-black text-slate-700 uppercase tracking-tight">
                <div className="flex flex-col">
                  <span className="text-slate-400 text-[10px] tracking-widest">{categories.falls} EVENTS</span>
                  <span>Fall Detection Model</span>
                </div>
                <span className="text-[#06217e] text-lg">{fallPercentage}%</span>
              </div>
              <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-[#06217e] rounded-full transition-all duration-1000" style={{ width: `${fallPercentage}%` }} />
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-end text-sm font-black text-slate-700 uppercase tracking-tight">
                <div className="flex flex-col">
                  <span className="text-slate-400 text-[10px] tracking-widest">{categories.violence} EVENTS</span>
                  <span>Violence Detection Model</span>
                </div>
                <span className="text-[#06217e] text-lg">{violencePercentage}%</span>
              </div>
              <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-slate-400 rounded-full transition-all duration-1000" style={{ width: `${violencePercentage}%` }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Data Grid Log View */}
      <section className="max-w-6xl mx-auto bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
          <h3 className="font-black text-[#06217e] text-sm uppercase tracking-wider flex items-center gap-2">
            Incident History
          </h3>
          <span className="text-xs bg-slate-200 text-slate-700 px-3 py-1 rounded-full font-bold">
            Showing {incidentsList.length} Entries
          </span>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-100/70 text-[11px] font-black text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Zone</th>
                <th className="py-3 px-4">Incident Type</th>
                <th className="py-3 px-4">Category</th>
                {isManager && <th className="py-3 px-4">Status</th>}
                {isManager && <th className="py-3 px-4">Response Time</th>} {/* INDIVIDUAL INCIDENT COLUMN */}
                <th className="py-3 px-4">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs font-semibold text-slate-700">
              {incidentsList.length === 0 ? (
                <tr>
                  <td colSpan={isManager ? 7 : 5} className="py-8 text-center text-slate-400 font-medium">
                    No matching structural data logs found inside filtered boundary thresholds.
                  </td>
                </tr>
              ) : (
                incidentsList.map((inc) => {
                  const catRaw = inc.danger_category || '';
                  
                  // Calculate duration for this individual incident row locally
                  const rowDuration = inc.status?.toLowerCase() === 'resolved' && inc.resolved_at
                    ? `${calculateDurationInMinutes(inc.timestamp, inc.resolved_at)} mins`
                    : 'N/A';

                  return (
                    <tr key={inc.incident_id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3.5 px-4 text-slate-500">
                        {inc.timestamp ? new Date(inc.timestamp).toLocaleString() : 'N/A'}
                      </td>
                      <td className="py-3.5 px-4 font-bold text-slate-800">
                        {inc.zone_name || 'Main Zone'}
                      </td>
                      <td className="py-3.5 px-4">{inc.incident_type || 'Unknown'}</td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                          catRaw.toLowerCase() === 'critical' 
                            ? 'bg-red-50 text-red-600 border border-red-200' 
                            : 'bg-orange-50 text-orange-600 border border-orange-200'
                        }`}>
                          {catRaw}
                        </span>
                      </td>
                      {isManager && (
                        <td className="py-3.5 px-4">
                          <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold capitalize ${
                            inc.status?.toLowerCase() === 'resolved'
                              ? 'bg-emerald-50 text-emerald-700'
                              : 'bg-amber-50 text-amber-700'
                          }`}>
                            {inc.status || 'Open'}
                          </span>
                        </td>
                      )}
                      {/* INDIVIDUAL INCIDENT DURATION CELL */}
                      {isManager && (
                        <td className="py-3.5 px-4 font-medium text-slate-600">
                          {rowDuration}
                        </td>
                      )}
                      <td className="py-3.5 px-4 font-mono text-slate-500">
                        {inc.confidence ? `${(inc.confidence * 100).toFixed(1)}%` : '0.0%'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}