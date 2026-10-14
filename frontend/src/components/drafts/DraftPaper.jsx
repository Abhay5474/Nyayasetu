/** The draft as it will look on paper (the server's blocks), so the person can read it before downloading. */
export default function DraftPaper({ doc }) {
  return (
    <article className="rounded-xl border border-ink-200 bg-white px-5 py-6 text-[13.5px] leading-relaxed text-ink-900 shadow-soft sm:px-8" lang={doc.language}>
      {doc.blocks.map((b, i) => {
        switch (b.type) {
          case 'title':
            return <h2 key={i} className="my-3 text-center text-base font-bold">{b.text}</h2>;
          case 'subtitle':
            return <p key={i} className="mb-1 text-center text-xs text-ink-600">{b.text}</p>;
          case 'box':
            return (
              <div key={i} className="mb-2 flex justify-end">
                <div className="max-w-[16rem] border border-ink-700 px-3 py-2 text-xs">{b.text}</div>
              </div>
            );
          case 'rows':
            return (
              <table key={i} className="my-3 w-full border-collapse text-[13px]">
                <tbody>
                  {b.rows.map(([k, v], j) =>
                    v ? (
                      <tr key={j}>
                        <td className="w-2/5 border border-ink-400 px-2 py-1.5 align-top">{k}</td>
                        <td className="whitespace-pre-line border border-ink-400 px-2 py-1.5 align-top">{v}</td>
                      </tr>
                    ) : (
                      <tr key={j}><td colSpan={2} className="border border-ink-400 px-2 py-1.5 font-bold">{k}</td></tr>
                    ),
                  )}
                </tbody>
              </table>
            );
          case 'numbered':
            return <div key={i} className="mb-2 space-y-1.5">{b.items.map((t, j) => <p key={j}>{t}</p>)}</div>;
          case 'signature':
            return <p key={i} className="mt-4 whitespace-pre-line text-right">{b.text}</p>;
          case 'right':
            return <p key={i} className="whitespace-pre-line text-right">{b.text}</p>;
          case 'spacer':
            return <div key={i} className="h-3" />;
          default:
            return <p key={i} className={`mb-2 whitespace-pre-line ${b.bold ? 'font-bold' : ''}`}>{b.text}</p>;
        }
      })}
    </article>
  );
}
