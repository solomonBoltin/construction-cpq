
import React from 'react';
import { QuotePreview, QuoteStatus } from '../../types';

interface QuoteCardProps {
  quote: QuotePreview;
  onSelect: (quoteId: number) => void;
}

const QuoteCard: React.FC<QuoteCardProps> = ({ quote, onSelect }) => {
  const statusStyles: Record<string, string> = {
    [QuoteStatus.DRAFT]: "bg-yellow-100 text-yellow-800",
    [QuoteStatus.CALCULATED]: "bg-blue-100 text-blue-800",
    [QuoteStatus.FINAL]: "bg-green-100 text-green-800"
  };

  const currentStatusStyle = statusStyles[quote.status.toUpperCase()] || "bg-slate-100 text-slate-800";


  return (
    <div
      onClick={() => onSelect(quote.id)}
      className="bg-white rounded-xl shadow-lg hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 cursor-pointer overflow-hidden fade-in"
      data-action="select-quote"
      data-quote-id={quote.id}
    >
      <div className="p-6">
        <div className="flex justify-between items-start mb-2">
          <h2 className="text-xl font-bold text-slate-900 truncate pr-2" title={quote.name || "Unnamed Quote"}>{quote.name || "Unnamed Quote"}</h2>
          <span className={`text-xs font-semibold px-2 py-1 rounded-full whitespace-nowrap ${currentStatusStyle}`}>
            {quote.status.toUpperCase()}
          </span>
        </div>
        <p className="text-slate-600 text-sm mb-4 h-12 overflow-hidden text-ellipsis">
          {quote.description || "No description."}
        </p>
        <div className="text-xs text-slate-400">
          Last updated: {new Date(quote.updated_at).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
};

export default QuoteCard;
