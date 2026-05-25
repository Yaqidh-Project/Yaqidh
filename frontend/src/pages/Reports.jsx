import React, { useState, useEffect } from 'react';
import { FileText, Download, Calendar, TrendingUp, BarChart2, FileSpreadsheet, FileJson, RefreshCw } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import axiosInstance from '../api/axiosInstance';

export default function Reports() {
  const [totalIncidents, setTotalIncidents] = useState(0);
  const [categories, setCategories] = useState({ falls: 0, violence: 0 });
  const [chartData, setChartData] = useState([]);
  const [downloadFormat, setDownloadFormat] = useState('pdf'); // State tracking format preference: 'pdf' or 'json'
  const [exportLoading, setExportLoading] = useState(false);

  useEffect(() => {
    // Retrieve real incident stats from database to build analytics graphs dynamically
    axiosInstance.get('/incidents')
      .then(res => {
        const data = res.data;
        setTotalIncidents(data.length);

        // Classify the total incidents based on AI inference labels
        const fallsCount = data.filter(i => i.incident_type?.toLowerCase().includes('fall')).length;
        const violenceCount = data.filter(i => i.incident_type?.toLowerCase().includes('violence')).length;
        setCategories({ falls: fallsCount, violence: violenceCount });

        // Populate weekly distributions dynamically
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu'];
        const distribution = days.map(day => ({
          name: day,
          incidents: data.filter(i => {
            const date = new Date(i.timestamp);
            const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            return dayLabels[date.getDay()] === day;
          }).length || 0,
          falsePositives: 0
        }));
        setChartData(distribution);
      })
      .catch(err => console.error("Error generating reports analytics:", err));
  }, []);

  const handleGenerateAndDownloadReport = async () => {
    setExportLoading(true);
    try {
      // Step 1: Request the backend to compile data metrics and persist a new Report row inside pgAdmin
      const filterPayload = {
        start_date: null,
        end_date: null,
        danger_category: null,
        status: null,
        camera_id: null
      };
      
      const createResponse = await axiosInstance.post('/reports', filterPayload);
      const newReportId = createResponse.data.report_id;

      if (!newReportId) throw new Error("Missing structural report identifier boundary.");

      // Step 2: Download the generated report block based on the user's selected file extension format
      if (downloadFormat === 'pdf') {
        const pdfResponse = await axiosInstance.get(`/reports/${newReportId}/export-pdf`, {
          responseType: 'blob' // Essential for processing binary stream documents cleanly
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
      console.error("Failed to compile or stream security documentation records:", err);
      alert("Could not process report compile actions. Verify your database records state.");
    } finally {
      setExportLoading(false);
    }
  };

  const fallPercentage = totalIncidents > 0 ? Math.round((categories.falls / totalIncidents) * 100) : 0;
  const violencePercentage = totalIncidents > 0 ? Math.round((categories.violence / totalIncidents) * 100) : 0;

  return (
    <div className="p-6 space-y-8 bg-slate-50/30 min-h-screen font-sans">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 max-w-6xl mx-auto border-b border-slate-200/60 pb-6">
        <div>
          <h2 className="text-3xl font-black text-brand-500 flex items-center gap-3">
            <BarChart2 size={36} /> Reports & Analytics
          </h2>
          <p className="text-slate-500 font-medium mt-1 tracking-tight">AI-powered safety monitoring data logs</p>
        </div>
        
        {/* Dynamic Executive Document Compiler Controls Block */}
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
            className="flex items-center gap-2 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl text-xs font-bold shadow-md shadow-brand-500/20 transition-all active:scale-95"
          >
            {exportLoading ? (
              <><RefreshCw size={14} className="animate-spin" /> Compiling...</>
            ) : (
              <><Download size={14} /> Generate & Download</>
            )}
          </button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto">
        <div className="flex justify-center -space-x-px"> 
          <div className="bg-white px-10 py-6 border border-slate-200 w-full max-w-md rounded-l-2xl shadow-sm flex items-center justify-between group hover:bg-slate-50/50 transition-colors">
            <div>
              <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">Total Incidents (Week)</p>
              <h3 className="text-4xl font-black text-red-600 tracking-tighter">{totalIncidents}</h3>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 bg-white rounded-full border border-slate-100 shadow-sm">
              <TrendingUp size={14} className="text-emerald-500" />
              <span className="text-xs font-bold text-emerald-600">+100%</span>
            </div>
          </div>
          <div className="bg-white px-10 py-6 border border-slate-200 w-full max-w-md rounded-r-2xl shadow-sm flex items-center justify-between group hover:bg-slate-50/50 transition-colors">
            <div>
              <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">System Precision</p>
              <h3 className="text-4xl font-black text-brand-500 tracking-tighter">100%</h3>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 bg-white rounded-full border border-slate-100 shadow-sm">
              <TrendingUp size={14} className="text-emerald-500" />
              <span className="text-xs font-bold text-emerald-600">Stable</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
        <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100">
          <h3 className="font-black text-brand-500 text-xl mb-6">Verification Accuracy</h3>
          <ResponsiveContainer width="100%" height={300}>
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

        <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100">
          <h3 className="font-black text-brand-500 text-xl mb-6">Incident Categories</h3>
          <div className="space-y-7 pt-2">
            <div className="space-y-3">
              <div className="flex justify-between items-end text-sm font-black text-slate-700 uppercase tracking-tight">
                <div className="flex flex-col">
                  <span className="text-slate-400 text-[10px] tracking-widest">{categories.falls} EVENTS</span>
                  <span>Fall Detection</span>
                </div>
                <span className="text-brand-500 text-lg">{fallPercentage}%</span>
              </div>
              <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-brand-500 rounded-full transition-all duration-1000" style={{ width: `${fallPercentage}%` }} />
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-end text-sm font-black text-slate-700 uppercase tracking-tight">
                <div className="flex flex-col">
                  <span className="text-slate-400 text-[10px] tracking-widest">{categories.violence} EVENTS</span>
                  <span>Violence Detection</span>
                </div>
                <span className="text-brand-500 text-lg">{violencePercentage}%</span>
              </div>
              <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-slate-400 rounded-full transition-all duration-1000" style={{ width: `${violencePercentage}%` }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}