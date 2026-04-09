import React, { useState } from 'react';
import { IntakePathA } from './IntakePathA';
import { IntakePathB } from './IntakePathB';

export function IntakePage() {
    const [activeTab, setActiveTab] = useState<'A' | 'B'>('A');

    return (
        <div className="h-full w-full overflow-y-auto p-8 pr-12">
            <div className="mb-8">
                <h1 className="text-3xl font-bold tracking-tight mb-2">Mandate Intake</h1>
                <p className="text-muted-foreground">Define the strict constraint boundaries Aegis uses to scout autonomous strategies.</p>
            </div>

            <div className="flex bg-muted/30 p-1 rounded-lg w-fit mb-8 border border-border/50">
                <button
                    onClick={() => setActiveTab('A')}
                    className={`px-6 py-2 rounded-md text-sm font-semibold transition-all ${
                        activeTab === 'A' ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                    }`}
                >
                    Path A: Guided Inputs
                </button>
                <button
                    onClick={() => setActiveTab('B')}
                    className={`px-6 py-2 rounded-md text-sm font-semibold transition-all ${
                        activeTab === 'B' ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                    }`}
                >
                    Path B: JSON Schema Payload
                </button>
            </div>

            <div className="w-full pb-16">
                {activeTab === 'A' ? <IntakePathA /> : <IntakePathB />}
            </div>
        </div>
    );
}
