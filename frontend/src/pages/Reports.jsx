import React, { useState } from 'react';
import { FileText, Download, Calendar, TrendingUp, Filter, BarChart2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

// Updated data: Removed Fri/Sat and set False Positives to 0 for Sun, Mon, Thu
const reportData = [
  { name: 'Sun', incidents: 2, falsePositives: 0 },
  { name: 'Mon', incidents: 3, falsePositives: 0 },
  { name: 'Tue', incidents: 2, falsePositives: 1 },
  { name: 'Wed', incidents: 5, falsePositives: 2 },
  { name: 'Thu', incidents: 4, falsePositives: 0 },
];

const reportStats = [
  { title: 'Total Incidents (Week)', value: '23', trend: '+15%', color: 'text-red-600' },
  { title: 'System Precision', value: '84%', trend: '+2%', color: 'text-brand-500' },
];

const ReportCard = ({ title, description, date, type }) => (
  <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow cursor-pointer group">
    <div className="flex items-start justify-between mb-4">
      <div className="flex items-start gap-3">
        <div className="p-3 rounded-xl bg-brand-50">
          <FileText size={20} className="text-brand-500" />
        </div>
        <div>
          <h3 className="font-bold text-slate-800">{title}</h3>
          <p className="text-sm text-slate-500 mt-1">{description}</p>
        </div>
      </div>
      <Download size={20} className="text-slate-400 group-hover:text-brand-500 transition-colors" />
    </div>
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate-500 flex items-center gap-1 font-medium">
        <Calendar size={14} /> {date}
      </span>
      <span className="px-3 py-1 bg-brand-50 text-brand-500 rounded-full text-xs font-bold uppercase tracking-tight">{type}</span>
    </div>
  </div>
);

export default function Reports() {
  return (
    <div className="p-6 space-y-8 bg-slate-50/30 min-h-screen font-sans">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 max-w-6xl mx-auto">
        <div>
          <h2 className="text-3xl font-black text-brand-500 flex items-center gap-3">
            <BarChart2 size={36} /> Reports & Analytics
          </h2>
          <p className="text-slate-500 font-medium mt-1 tracking-tight">AI-powered safety monitoring data</p>
        </div>
        <button className="flex items-center gap-2 bg-brand-500 hover:bg-brand-600 text-white px-6 py-3 rounded-2xl font-bold shadow-lg shadow-brand-500/30 transition-all active:scale-95">
          <Download size={20} /> Export Dataset
        </button>
      </header>

      {/* Unified Wide Stats Section */}
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-center -space-x-px"> 
          {reportStats.map((stat, idx) => (
            <div 
              key={idx} 
              className={`bg-white px-10 py-6 border border-slate-200 w-full max-w-md
                ${idx === 0 ? 'rounded-l-2xl' : 'rounded-r-2xl'} 
                shadow-sm flex items-center justify-between group hover:bg-slate-50/50 transition-colors`}
            >
              <div>
                <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">
                  {stat.title}
                </p>
                <h3 className={`text-4xl font-black ${stat.color} tracking-tighter`}>
                  {stat.value}
                </h3>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 bg-white rounded-full border border-slate-100 shadow-sm">
                <TrendingUp size={14} className="text-emerald-500" />
                <span className="text-xs font-bold text-emerald-600">
                  {stat.trend}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Best-Practice Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
        
        {/* Verification Accuracy Chart */}
        <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-black text-brand-500 text-xl">Verification Accuracy</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={reportData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontWeight: 600}} />
              <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontWeight: 600}} />
              <Tooltip 
                cursor={{fill: '#f8fafc'}}
                contentStyle={{ borderRadius: '1rem', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
              />
              <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ paddingBottom: '20px', fontSize: '12px', fontWeight: 700 }} />
              <Bar name="Verified Incidents" dataKey="incidents" stackId="a" fill="#06217e" radius={[0, 0, 0, 0]} />
              <Bar name="False Positives" dataKey="falsePositives" stackId="a" fill="#e2e8f0" radius={[10, 10, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Category Breakdown */}
        <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100">
          <h3 className="font-black text-brand-500 text-xl mb-6">Incident Categories</h3>
          <div className="space-y-7 pt-2">
            {[
              { label: 'Fall Detection', value: 65, color: 'bg-brand-500', count: 15 },
             { label: 'Violence Detection', value: 35, color: 'bg-slate-400', count: 5 },
            ].map((item, i) => (
              <div key={i} className="space-y-3">
                <div className="flex justify-between items-end text-sm font-black text-slate-700 uppercase tracking-tight">
                  <div className="flex flex-col">
                    <span className="text-slate-400 text-[10px] tracking-widest">{item.count} EVENTS</span>
                    <span>{item.label}</span>
                  </div>
                  <span className="text-brand-500 text-lg">{item.value}%</span>
                </div>
                <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${item.color} rounded-full transition-all duration-1000`} 
                    style={{ width: `${item.value}%` }} 
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Advanced Filter Box */}
      <div className="bg-white p-10 rounded-[3rem] shadow-sm border border-slate-100 max-w-6xl mx-auto">
        <h3 className="text-xl font-black text-brand-500 mb-8 flex items-center gap-2">
          <Filter size={24} /> Precision Filtering
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="space-y-2">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-tighter ml-1">Start Date</label>
            <input type="date" className="w-full px-5 py-4 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 font-medium text-slate-600" />
          </div>
          <div className="space-y-2">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-tighter ml-1">End Date</label>
            <input type="date" className="w-full px-5 py-4 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 font-medium text-slate-600" />
          </div>
          <div className="space-y-2">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-tighter ml-1">Alert Category</label>
            <select className="w-full px-5 py-4 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 font-medium cursor-pointer text-slate-600">
              <option value="">All Categories</option>
              <option value="fall">Fall Detected</option>
              <option value="violence">Violence Detected</option>
            </select>
          </div>
          <div className="flex items-end">
            <button className="w-full bg-brand-500 hover:bg-brand-600 text-white font-black py-4 rounded-2xl shadow-lg shadow-brand-500/30 transition-transform active:scale-95 uppercase tracking-widest text-xs">
              Generate Report
            </button>
          </div>
        </div>
      </div>

      {/* Archive Section */}
      <div className="max-w-6xl mx-auto pb-10">
        <h3 className="text-xl font-black text-brand-500 mb-6">Generated Summaries</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ReportCard title="Daily Safety Review" description="Overview of behavior classification results" date="May 13, 2026" type="Daily" />
          <ReportCard title="Monthly Performance" description="Model accuracy and incident response tracking" date="May 01, 2026" type="Technical" />
        </div>
      </div>
    </div>
  );
}