import { SquareSquare } from "lucide-react";

export function GlassBoxInspector() {
    return (
        <div className="h-full w-full rounded-md border border-border bg-card/50 backdrop-blur-sm overflow-hidden flex flex-col">
            <div className="p-3 border-b border-border bg-black/40 flex items-center gap-2">
                <SquareSquare className="w-4 h-4 text-blue-400" />
                <h2 className="text-sm font-medium text-foreground">Glass Box Audit Trail: Alpha-Macro-1</h2>
            </div>
            <div className="flex-1 grid grid-cols-12 gap-0 h-full w-full">
                {/* Left Panel: The Mind (Streaming LLM Text) */}
                <div className="col-span-5 h-full w-full bg-[#0d0d12]/80 p-4 border-r border-border flex flex-col">
                    <h3 className="text-xs font-semibold text-blue-400 uppercase tracking-widest mb-4">The Mind (Analyst Trace)</h3>
                    <div className="flex-1 border border-border/50 rounded-md bg-black/30 p-4 overflow-y-auto font-mono text-sm text-gray-300">
                        <p className="text-gray-500 mb-2">[09:30:12 AM] Trigger: Market Open.</p>
                        <p className="mb-2">Observed HMM Regime: <span className="bg-green-500/20 text-green-400 px-1 rounded cursor-pointer hover:underline">Bullish</span></p>
                        <p className="mb-2">Observed Order Flow Toxicity: <span className="bg-blue-500/20 text-blue-400 px-1 rounded cursor-pointer hover:underline">VPIN = 0.12 (Normal)</span></p>
                        <p className="mb-2 text-primary">Synthesizing macro data... Market conditions are favorable for long exposure on tech mega-caps.</p>
                        <p className="text-green-400 font-bold mt-4">&gt; EXECUTING LONG AAPL</p>
                    </div>
                </div>

                {/* Right Panels: The Math & The Evidence */}
                <div className="col-span-7 h-full w-full grid grid-rows-12 gap-0 bg-[#0d0d12]">
                    {/* Top Right: Hard Quant Gauges at time of trade */}
                    <div className="row-span-5 h-full w-full bg-[#14141b]/80 p-4 border-b border-border flex flex-col">
                        <h3 className="text-xs font-semibold text-cyan-400 uppercase tracking-widest mb-4">The Math (Quant Engine Point-in-Time)</h3>
                        <div className="flex-1 flex items-center justify-center text-sm text-gray-500 italic border border-border/50 rounded-md bg-black/30">
                            Hover over a citation in The Mind to see the hard math here.
                        </div>
                    </div>

                    {/* Bottom Right: Financial Charts & Evidence */}
                    <div className="row-span-7 h-full w-full bg-[#0d0d12] p-4 flex flex-col">
                        <h3 className="text-xs font-semibold text-purple-400 uppercase tracking-widest mb-4">The Evidence (Charts & Filings)</h3>
                        <div className="flex-1 flex items-center justify-center text-sm text-gray-500 italic border border-border/50 rounded-md bg-black/30">
                            Relevant charts and SEC filings will appear here.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
