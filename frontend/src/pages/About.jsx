import React from "react";
import {
  ShieldCheck,
  Users,
  Camera,
  Smartphone,
  Zap,
  FileBarChart,
  Mail,
  Cpu,
  Sparkles,
  Building,
  Home as HomeIcon,
  ArrowRight,
  BellRing,
  BrainCircuit,
  Eye,
  CheckCircle2,
} from "lucide-react";

const features = [
  {
    title: "AI Incident Detection",
    description:
      "Real-time intelligent monitoring powered by advanced computer vision and deep learning models.",
    icon: BrainCircuit,
  },
  {
    title: "Smart Notifications",
    description:
      "Instant alerts and live updates sent directly to Emails and dashboards.",
    icon: BellRing,
  },
  {
    title: "Role-Based Access Control",
    description:
      "Security architecture with encrypted communication and role-based access.",
    icon: ShieldCheck,
  },
  {
    title: "Multi-Camera Integration",
    description:
      "Connect and manage multiple surveillance feeds from one centralized system.",
    icon: Camera,
  },
  {
    title: "Environmental Adaptability",
    description:
      "The AI models were validated using diverse environmental variations including motion blur, shadows, and changing nursery lighting conditions to maintain reliable performance in real-world childcare spaces.",
    icon: FileBarChart,
  },
  {
    title: "Efficient Infrastructure",
    description:
      "Designed to operate efficiently on standard computing hardware without requiring expensive high-end graphics processing systems or complex infrastructure setups.",
    icon: Cpu,
  },
  {
    title: "Analytical Reporting",
    description:
      "Generates secure, comprehensive safety audits. Users can filter historical trends by date or category and export data into clean PDF documents.",
    icon: FileBarChart,
  },
  {
    title: "Data Privacy Integrity",
    description:
      "The system completely bypasses facial profiling and identity tracking. Short recordings of detected events are securely held within a private database.",
    icon: Eye,
  },
];

const methodology = [
  {
    title: "AI Model Training",
    description:
      "The models are trained to recognize behavioral patterns, posture changes, and aggressive actions while optimizing detection precision for real-time monitoring.",
    icon: BrainCircuit,
  },
  {
    title: "Live Monitoring",
    description:
      "The platform continuously analyzes camera streams and monitors environments instantly.",
    icon: Eye,
  },
  {
    title: "Instant Response",
    description:
      "When an incident is detected, alerts and notifications are immediately sent to responsible authorities.",
    icon: Zap,
  },
    {
    title: "Secure Incident Storage",
    description:
      "When an incident is detected, a short clip of the event is securely stored inside a private database and can be reviewed later by responsible authorities such as parents or nursery managers.",
    icon: FileBarChart,
  },
];

function FloatingBlur({ className }) {
  return (
    <div
      className={`absolute rounded-full blur-3xl opacity-30 animate-pulse ${className}`}
    />
  );
}

function FeatureCard({ icon: Icon, title, description }) {
  return (
    <div className="group relative overflow-hidden rounded-3xl border border-slate-100 bg-white p-6 shadow-md transition-all duration-500 hover:-translate-y-2 hover:shadow-xl">
      <div className="absolute inset-0 bg-gradient-to-br from-[#06217e]/5 via-transparent to-slate-50 opacity-0 transition-opacity duration-500 group-hover:opacity-100" />

      <div className="relative z-10">
        <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#06217e]/10 text-[#06217e] transition-all duration-300 group-hover:scale-110 group-hover:bg-[#06217e] group-hover:text-white">
          <Icon className="h-7 w-7" />
        </div>

        <h3 className="mb-3 text-xl font-bold text-slate-900">
          {title}
        </h3>

        <p className="leading-relaxed text-slate-600 text-sm">
          {description}
        </p>
      </div>
    </div>
  );
}

function MethodCard({ icon: Icon, title, description }) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white/80 p-6 backdrop-blur-md transition-all duration-300 hover:-translate-y-2 hover:border-[#06217e]/30 hover:shadow-xl">
      <div className="flex flex-col items-center text-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#06217e]/10 text-[#06217e] transition-all duration-300 group-hover:scale-110 group-hover:bg-[#06217e] group-hover:text-white">
          <Icon className="h-6 w-6" />
        </div>

        <p className="font-semibold text-slate-800 text-lg">
          {title}
        </p>

        <div className="mt-4 max-h-0 overflow-hidden opacity-0 transition-all duration-500 group-hover:max-h-40 group-hover:opacity-100">
          <p className="text-sm leading-relaxed text-slate-600">
            {description}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function About() {
  const scrollToFeatures = () => {
    const section = document.getElementById("features-section");

    if (section) {
      section.scrollIntoView({
        behavior: "smooth",
      });
    }
  };

  const scrollToContact = () => {
    const section = document.getElementById("contact-section");

    if (section) {
      section.scrollIntoView({
        behavior: "smooth",
      });
    }
  };

  return (
    <main className="relative overflow-hidden bg-gradient-to-b from-slate-50 via-white to-slate-100 text-slate-800 min-h-screen">
      {/* Background Graphic Blobs */}
      <FloatingBlur className="left-0 top-20 h-72 w-72 bg-blue-200/50" />
      <FloatingBlur className="right-0 top-96 h-80 w-80 bg-[#06217e]/5" />
      <FloatingBlur className="bottom-0 left-1/3 h-72 w-72 bg-indigo-200/50" />

      <div className="relative z-10 mx-auto max-w-7xl px-6 py-10 space-y-28">
        
        {/* HERO HEADER SECTION */}
        <section className="relative overflow-hidden rounded-[36px] border border-white/20 bg-gradient-to-br from-[#0a2fa6] via-[#082587] to-[#061b61] p-8 md:p-14 shadow-2xl shadow-blue-950/30">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.15),transparent_30%)]" />

          <div className="grid items-center gap-14 lg:grid-cols-2">
            {/* LEFT COLUMN */}
            <div className="relative z-10">
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium text-white backdrop-blur-md">
                <Sparkles className="h-4 w-4" />
                AI-Powered Smart Surveillance
              </div>

              <h1 className="text-3xl font-black leading-tight text-white md:text-5xl tracking-tight">
                Building a{" "}
                <span className="text-blue-200">Safer & Smarter</span>{" "}
                Childhood Environment with AI
              </h1>

              <p className="mt-6 max-w-xl text-lg leading-relaxed text-blue-100/90">
                Yaqidh transforms traditional surveillance into a modern
                AI-powered safety ecosystem with automated incident detection,
                instant alerts, and intelligent analytics.
              </p>

              <div className="mt-8 flex flex-wrap gap-4">
                <button
                  onClick={scrollToFeatures}
                  className="group inline-flex items-center gap-2 rounded-2xl bg-white px-6 py-3 font-semibold text-[#06217e] shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-2xl"
                >
                  Explore Features
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </button>

                <button
                  onClick={scrollToContact}
                  className="rounded-2xl border border-white/20 bg-white/10 px-6 py-3 font-semibold text-white backdrop-blur-md transition-all duration-300 hover:bg-white/20"
                >
                  Contact Us
                </button>
              </div>

              {/* DASHBOARD STATISTICS MOCKUP */}
              <div className="mt-10 grid grid-cols-3 gap-3">
                {[
                  { value: "90%", label: "Detection Accuracy" },
                  { value: "24/7", label: "Monitoring" },
                  { value: "Instant", label: "Alerts" },
                ].map((item) => (
                  <div
                    key={item.label}
                    className="rounded-2xl border border-white/10 bg-white/10 p-4 text-center backdrop-blur-md transition-all duration-300 hover:bg-white/20"
                  >
                    <div className="text-2xl font-black text-white">
                      {item.value}
                    </div>
                    <div className="mt-1 text-xs text-blue-100">
                      {item.label}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* RIGHT COLUMN */}
            <div className="relative">
              <div className="absolute -left-8 top-10 h-28 w-28 rounded-full bg-blue-400/20 blur-2xl" />
              <div className="absolute bottom-0 right-0 h-40 w-40 rounded-full bg-white/10 blur-3xl" />

              <div className="relative rounded-[32px] border border-white/10 bg-white/10 p-8 backdrop-blur-2xl shadow-2xl">
                <div className="mb-6 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-blue-200 uppercase tracking-wider">
                      Live Stream Feed
                    </p>
                    <h3 className="text-xl font-bold text-white mt-0.5">
                      Smart Security Tracking
                    </h3>
                  </div>

                  <div className="flex items-center gap-2 rounded-full bg-emerald-400/20 px-3 py-1 text-xs text-emerald-200 font-medium">
                    <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                    Active Pipeline
                  </div>
                </div>

                <div className="space-y-3">
                  {[
                    "AI detected suspicious activity",
                    "Instant notification sent to authorities",
                    "Secure event database storage linked",
                    "Emergency response system activated",
                  ].map((item, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-3 rounded-xl bg-white/5 p-3.5 backdrop-blur-md transition-all duration-300 hover:bg-white/10"
                    >
                      <CheckCircle2 className="h-5 w-5 text-emerald-300 flex-shrink-0" />
                      <p className="text-white text-sm">{item}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* The Core Intelligent Engine - Redesigned for Maximum Text Clarity */}
        <div className="bg-white rounded-3xl shadow-md border border-slate-100 p-8 transition-all hover:shadow-xl">
          <div className="flex items-center gap-3 mb-6 border-b border-slate-50 pb-4">
            <div className="p-3 bg-[#06217e]/10 rounded-2xl text-[#06217e]">
              <Cpu size={28} />
            </div>
            <h3 className="text-2xl font-bold text-slate-900">The Core Intelligent Engine</h3>
          </div>
          <p className="text-slate-600 leading-relaxed mb-8 text-base">
            Rather than relying on human screens or generic motion sensors, Yaqidh utilizes advanced computer vision to actively analyze behavioral patterns directly from live video feeds. Specifically tailored to recognize the movements and proportions of young children, the system operates continuously to detect two major safety risks:
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-50 rounded-2xl p-6 border border-slate-100/80 hover:bg-slate-100/50 transition-colors">
              <h4 className="font-bold text-slate-900 mb-3 text-lg flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#06217e]"></span>
                Automated Fall Detection
              </h4>
              <p className="text-slate-600 leading-relaxed text-sm">
                The system recognizes human body posture and immediately flags when a child slips, trips, or falls to the ground. This analysis is handled entirely through the video feed, meaning children do not need to wear uncomfortable tracking devices or electronic sensors.
              </p>
            </div>
            
            <div className="bg-slate-50 rounded-2xl p-6 border border-slate-100/80 hover:bg-slate-100/50 transition-colors">
              <h4 className="font-bold text-slate-900 mb-3 text-lg flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#06217e]"></span>
                Child Violence Detection
              </h4>
              <p className="text-slate-600 leading-relaxed text-sm">
                The system evaluates physical interactions in shared spaces. It can differentiate between standard, energetic play and sudden aggressive behaviors, such as pushing, hitting, kicking, or physical disputes alerting supervisors immediately to manage child safety.
              </p>
            </div>
          </div>
        </div>

        {/* CORE SYSTEM FEATURES SECTION - RE-ORDERED INTO A 3x2 UNIFIED GRID */}
        <section id="features-section">
          <div className="mb-14 text-center">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-[#06217e]/5 px-4 py-1.5 text-xs font-bold text-[#06217e] uppercase tracking-wider border border-[#06217e]/10">
              <ShieldCheck className="h-3.5 w-3.5" />
              System Architecture
            </div>

            <h2 className="text-3xl md:text-4xl font-black text-slate-900 tracking-tight">
              Intelligent Features Designed for Modern Security
            </h2>

            <p className="mx-auto mt-4 max-w-3xl text-base leading-relaxed text-slate-500">
              Combining computer vision inference pipelines, real-time tracking dashboards, 
              and automated email routing rules into a unified, secure childhood safety framework.
            </p>
          </div>

          {/* Balanced Row Grid layout to support structural 3-3 configuration layout */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <FeatureCard
                key={feature.title}
                icon={feature.icon}
                title={feature.title}
                description={feature.description}
              />
            ))}
          </div>
        </section>

        {/* OPERATION METHODOLOGY METHOD FLOW CARD CONTAINER */}
        <section className="relative overflow-hidden rounded-[36px] border border-slate-100 bg-white p-8 shadow-xl md:p-12">
          <div className="absolute right-0 top-0 h-60 w-60 rounded-full bg-[#06217e]/5 blur-3xl pointer-events-none" />

          <div className="relative z-10">
            <div className="mb-14 text-center">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-[#06217e]/5 px-4 py-1.5 text-xs font-bold text-[#06217e] uppercase tracking-wider border border-[#06217e]/10">
                <Cpu className="h-3.5 w-3.5" />
                Workflow Methodology
              </div>

              <h2 className="text-3xl md:text-4xl font-black text-slate-900 tracking-tight">
                How The Intelligent System Operates
              </h2>

              <p className="mx-auto mt-4 max-w-2xl text-base text-slate-500">
                Our lightweight processing flow handles frame inputs efficiently, mapping live behavior 
                and dispatching risk alerts seamlessly across custom target child tracking sets.
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              {methodology.map((item) => (
                <MethodCard
                  key={item.title}
                  icon={item.icon}
                  title={item.title}
                  description={item.description}
                />
              ))}
            </div>
          </div>
        </section>

        {/* FOOTER SPLIT: MISSION PROFILE & CORRESPONDENCE INTERFACE */}
        <section className="grid gap-8 lg:grid-cols-2">
          {/* MISSION CONTEXT WRAPPER */}
          <div className="relative overflow-hidden rounded-[30px] bg-[#06217e] p-8 text-white shadow-xl flex flex-col justify-between">
            <div className="absolute right-0 top-0 h-52 w-52 rounded-full bg-white/5 blur-3xl pointer-events-none" />

            <div className="relative z-10">
              <div className="mb-5 inline-flex rounded-full bg-white/10 px-4 py-1.5 text-xs font-bold tracking-wider uppercase border border-white/10">
                Our Mission
              </div>

              <h3 className="text-3xl font-black leading-tight tracking-tight">
                Creating safer communities through intelligent technology.
              </h3>

              <p className="mt-4 leading-relaxed text-blue-100/80 text-sm">
                We transform childcare environment frameworks using automated vision metrics that support on-duty 
                supervisors, keeping parental tracking transparent without relying on continuous visual screen checking.
              </p>
            </div>

            <div className="mt-8 grid grid-cols-2 gap-4 relative z-10">
              {[
                { icon: BrainCircuit, label: "AI Incident Detection" },
                { icon: BellRing, label: "Smart Notifications" },
                { icon: ShieldCheck, label: "Role-Based Access Control" },
                { icon: Camera, label: "Multi-Camera Integration" },              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div
                    key={item.label}
                    className="rounded-2xl bg-white/5 p-4 border border-white/10 transition-all duration-300 hover:bg-white/10 hover:scale-105"
                  >
                    <Icon className="mb-2 h-5 w-5 text-blue-200" />
                    <p className="text-xs font-semibold text-white tracking-wide">{item.label}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* CONTACT CORRESPONDENCE INTERFACE */}
          <div
            id="contact-section"
            className="rounded-[30px] border border-slate-100 bg-white p-8 shadow-xl"
          >
            <div className="mb-6 flex items-center gap-4">
              <div className="rounded-2xl bg-[#06217e]/5 p-3.5 text-[#06217e] border border-[#06217e]/10">
                <Mail className="h-6 w-6" />
              </div>

              <div>
                <h3 className="text-2xl font-black text-slate-900 tracking-tight">
                  Get In Touch
                </h3>
                <p className="text-sm text-slate-500 mt-0.5">
                  Contact us anytime at{" "}
                  <a
                    href="mailto:YaqidhTeam@gmail.com"
                    className="font-bold text-[#06217e] hover:underline"
                  >
                    YaqidhTeam@gmail.com
                  </a>
                </p>
              </div>
            </div>

            <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
              <div>
                <label className="mb-1.5 block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Full Name
                </label>
                <input
                  type="text"
                  placeholder="Enter your name"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-2.5 text-sm outline-none transition-all duration-300 focus:border-[#06217e] focus:bg-white focus:ring-4 focus:ring-[#06217e]/5"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Email Address
                </label>
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-2.5 text-sm outline-none transition-all duration-300 focus:border-[#06217e] focus:bg-white focus:ring-4 focus:ring-[#06217e]/5"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Message
                </label>
                <textarea
                  rows={4}
                  placeholder="Write your message..."
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-2.5 text-sm outline-none transition-all duration-300 focus:border-[#06217e] focus:bg-white focus:ring-4 focus:ring-[#06217e]/5"
                />
              </div>

              <button
                type="submit"
                className="group inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#06217e] px-6 py-3.5 font-bold text-white shadow-lg shadow-[#06217e]/20 transition-all duration-300 hover:scale-[1.01] hover:shadow-xl"
              >
                Send Message
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </button>
            </form>
          </div>
        </section>

      </div>
    </main>
  );
}