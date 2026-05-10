import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

export function LLMIntakePage() {
  const [selectedFile, setSelectedFile] = useState<string>('START_HERE.txt');
  const [fileContent, setFileContent] = useState<string>('');

  const files = [
    'START_HERE.txt',
    '1_llm_guide.md',
    '2_blank_schema.json',
    '3_example_schema.json'
  ];

  useEffect(() => {
    // We still fetch content for preview from the public folder or we could fetch from the backend static mount
    fetch(`/aegis_intake_package/${selectedFile}`)
      .then(res => res.text())
      .then(text => setFileContent(text))
      .catch(err => setFileContent('Error loading file.'));
  }, [selectedFile]);

  const renderContent = () => {
    if (selectedFile.endsWith('.md')) {
      return (
        <div className="prose prose-invert max-w-none prose-sm prose-p:text-[#8e8e88] prose-headings:text-on-surface prose-strong:text-on-surface prose-code:text-primary prose-pre:bg-transparent prose-pre:p-0">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{fileContent}</ReactMarkdown>
        </div>
      );
    }
    if (selectedFile.endsWith('.json')) {
      return (
        <SyntaxHighlighter
          language="json"
          style={vscDarkPlus}
          customStyle={{ background: 'transparent', padding: 0, margin: 0 }}
          wrapLongLines={true}
        >
          {fileContent}
        </SyntaxHighlighter>
      );
    }
    return (
      <pre className="text-sm text-on-surface-variant font-mono whitespace-pre-wrap">
        {fileContent}
      </pre>
    );
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-32">
      {/* HEADER */}
      <div>
        <h1 className="font-headline text-4xl font-light tracking-tight text-on-surface">
          LLM Intake Configuration
        </h1>
        <p className="text-[#8e8e88] mt-2 max-w-2xl leading-relaxed">
          Already using an LLM to do market research? Use this feature to have your LLM fill out your Aegis pipeline config. Download the zipped folder, upload it to your LLM agent, and then upload the resulting schema back here.
        </p>
      </div>

      {/* DOWNLOAD BAR */}
      <div className="bg-surface-container-low border border-secondary/20 rounded-xl p-8 flex items-center justify-between">
        <div>
          <h2 className="text-xl text-on-surface font-medium">1. Download Intake Package</h2>
          <p className="text-sm text-[#8e8e88] mt-1">Extract this package to conduct your LLM-guided interview. Served via Aegis API.</p>
        </div>
        <a
          href="http://localhost:8000/api/intake/download-package"
          target="_blank"
          rel="noopener noreferrer"
          className="px-6 py-3 bg-primary-container text-on-primary-container text-[0.8125rem] font-semibold rounded-lg hover:brightness-110 transition-all flex items-center gap-2 shadow-sm"
        >
          <span className="material-symbols-outlined text-[18px]">download</span>
          Download Package .zip
        </a>
      </div>

      {/* PREVIEW BOX WITH SIDEBAR INSTRUCTIONS */}
      <div className="bg-surface-container border border-white/10 rounded-xl overflow-hidden shadow-2xl">
        {/* TOP BAR */}
        <div className="flex items-center justify-between border-b border-white/10 bg-surface/50 px-6 py-3">
           <div className="text-[0.625rem] font-bold uppercase tracking-[0.2em] text-[#8e8e88]">
             File Contents preview
           </div>
           <div className="flex gap-2">
             {files.map(file => (
               <button
                 key={file}
                 onClick={() => setSelectedFile(file)}
                 className={`px-4 py-1.5 rounded-lg text-[0.75rem] font-medium transition-all ${
                   selectedFile === file
                     ? 'bg-white/10 text-white shadow-sm'
                     : 'text-[#8e8e88] hover:text-on-surface hover:bg-white/5'
                 }`}
               >
                 <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-[14px]">
                      {file.endsWith('.json') ? 'data_object' : file.endsWith('.md') ? 'markdown' : 'description'}
                    </span>
                    {file}
                 </div>
               </button>
             ))}
           </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 h-[700px]">
          {/* LEFT SIDEBAR: INSTRUCTIONS */}
          <div className="md:col-span-1 border-r border-white/10 bg-surface/30 p-8 space-y-6 overflow-y-auto scrollbar-thin">
            <h3 className="text-[0.6875rem] font-bold uppercase tracking-[0.2em] text-primary">Instructions</h3>
            <div className="space-y-6">
              {[
                "Download your intake package",
                "Open Claude, ChatGPT, or Gemini and start a new conversation",
                "Upload all four files from the package",
                "Submit it to the chat",
                "Answer the AI's questions — it will guide you through your mandate setup",
                "When finished, the AI will produce a file called aegis_mandate.json — download it and upload it below. If your AI couldn't generate a file, it will output a labeled text block instead — copy and paste that below."
              ].map((step, i) => (
                <div key={i} className="flex gap-4">
                  <div className="w-5 h-5 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-[10px] text-primary font-bold shrink-0">{i+1}</div>
                  <p className="text-[0.8125rem] text-[#8e8e88] leading-relaxed">{step}</p>
                </div>
              ))}
            </div>
          </div>

          {/* MAIN PREVIEW AREA */}
          <div className="md:col-span-3 bg-[#0d0d0c] p-10 overflow-y-auto scrollbar-thin">
            {renderContent()}
          </div>
        </div>
      </div>

      {/* UPLOAD SECTION */}
      <div className="bg-surface-container rounded-xl border border-white/5 p-8 flex flex-col items-center justify-center min-h-[200px] text-center">
        <span className="material-symbols-outlined text-[40px] text-[#8e8e88]/30 mb-3">upload_file</span>
        <h2 className="text-lg text-on-surface font-medium">Upload Completed Mandate</h2>
        <p className="text-sm text-[#8e8e88] mt-2 mb-4 max-w-md">
          Once your LLM has generated the <code className="text-primary text-[12px]">aegis_mandate.json</code> file, upload it here to validate and lock your mandate.
        </p>
        <button disabled className="px-6 py-2.5 border border-white/10 text-[#8e8e88] bg-white/5 text-[0.8125rem] font-medium rounded-lg cursor-not-allowed flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px]">upload</span>
          Upload Mandate (Coming Soon)
        </button>
      </div>

      <style dangerouslySetInnerHTML={{ __html: `
        .prose h1, .prose h2, .prose h3 { margin-top: 1.5em; margin-bottom: 0.5em; }
        .prose p { margin-bottom: 1.2em; line-height: 1.8; }
        .prose ul, .prose ol { margin-bottom: 1.2em; padding-left: 1.5em; list-style-type: disc; }
        .prose li { margin-bottom: 0.6em; }
        .prose hr { border-top: 1px solid rgba(255,255,255,0.1); margin: 2em 0; }
        .prose table { width: 100%; border-collapse: collapse; margin-bottom: 1em; font-size: 0.8rem; }
        .prose th, .prose td { border: 1px solid rgba(255,255,255,0.1); padding: 8px; text-align: left; }
        .prose th { background: rgba(255,255,255,0.05); color: #fff; }
      `}} />

    </div>
  );
}
