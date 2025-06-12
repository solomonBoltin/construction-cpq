'use client'; // Add this at the top for client-side interactivity

import Image from "next/image";
import { useEffect, useState, ChangeEvent, FormEvent } from "react"; // Added ChangeEvent, FormEvent
import { listQuotes, createQuote, QuotePreview, CreateQuotePayload } from '../services/api'; // Adjust path as needed

export default function Home() {
  const [quotes, setQuotes] = useState<QuotePreview[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newQuoteName, setNewQuoteName] = useState('');
  const [newQuoteType, setNewQuoteType] = useState('STANDARD'); // Default quote type

  const fetchQuotes = async () => {
    try {
      setIsLoading(true);
      const fetchedQuotes = await listQuotes();
      setQuotes(fetchedQuotes);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQuotes();
  }, []);

  const handleCreateQuote = async (e: FormEvent<HTMLFormElement>) => { // Corrected type
    e.preventDefault();
    if (!newQuoteName.trim()) {
      setError("Quote name cannot be empty.");
      return;
    }
    setIsLoading(true); // Set loading true during API call
    try {
      const payload: CreateQuotePayload = {
        name: newQuoteName,
        quote_type: newQuoteType,
        // description: "Optional description here", // Add if you have an input for it
      };
      await createQuote(payload);
      setNewQuoteName(''); // Reset input
      // setNewQuoteType('STANDARD'); // Reset select if needed
      fetchQuotes(); // Refresh the list
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create quote');
    } finally {
      setIsLoading(false); // Set loading false after API call
    }
  };

  return (
    <div className="grid grid-rows-[auto_1fr_auto] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <header className="flex flex-col items-center gap-4 mb-8">
        <Image
          className="dark:invert"
          src="/next.svg"
          alt="Next.js logo"
          width={180}
          height={38}
          priority
        />
        <h1 className="text-3xl font-semibold">Quote Management</h1>
      </header>

      <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start w-full max-w-2xl">
        <form onSubmit={handleCreateQuote} className="mb-8 p-4 border rounded shadow-md w-full bg-white dark:bg-gray-800">
          <h2 className="text-xl font-semibold mb-3 text-gray-800 dark:text-white">Create New Quote</h2>
          {error && <p className="text-red-500 bg-red-100 dark:bg-red-900 dark:text-red-200 p-2 rounded mb-3">{error}</p>}
          <div className="mb-4">
            <label htmlFor="quoteName" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Quote Name:
            </label>
            <input
              type="text"
              id="quoteName"
              value={newQuoteName}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setNewQuoteName(e.target.value)} // Corrected type
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
              placeholder="Enter quote name"
              disabled={isLoading} // Disable input when loading
            />
          </div>
          <div className="mb-4">
            <label htmlFor="quoteType" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Quote Type:
            </label>
            <select
              id="quoteType"
              value={newQuoteType}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => setNewQuoteType(e.target.value)} // Corrected type
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              disabled={isLoading} // Disable select when loading
            >
              <option value="STANDARD">Standard</option>
              <option value="CUSTOM">Custom</option>
              {/* Add other quote types from your QuoteType enum as needed */}
            </select>
          </div>
          <button
            type="submit"
            className="rounded-md border border-solid border-transparent bg-blue-600 text-white px-4 py-2 hover:bg-blue-700 transition-colors font-medium text-sm disabled:opacity-50"
            disabled={isLoading || !newQuoteName.trim()} // Disable button when loading or name is empty
          >
            {isLoading && !quotes.length ? 'Creating...' : 'Create Quote'} {/* More specific loading text */}
          </button>
        </form>

        <h2 className="text-2xl font-semibold mb-4 self-start text-gray-800 dark:text-white">Existing Quotes</h2>
        {isLoading && !quotes.length ? (
          <p className="text-gray-600 dark:text-gray-400">Loading quotes...</p>
        ) : !isLoading && quotes.length === 0 ? (
          <p className="text-gray-600 dark:text-gray-400">No quotes found. Create one above!</p>
        ) : (
          <ul className="list-none w-full space-y-3">
            {quotes.map((quote) => (
              <li key={quote.id} className="p-3 border rounded shadow-sm hover:shadow-md transition-shadow bg-white dark:bg-gray-800">
                <h3 className="text-lg font-medium text-blue-700 dark:text-blue-400">{quote.name || 'Unnamed Quote'}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">Type: {quote.quote_type}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Status: {quote.status}</p>
                <p className="text-xs text-gray-500 dark:text-gray-500">Last Updated: {new Date(quote.updated_at).toLocaleString()}</p>
              </li>
            ))}
          </ul>
        )}
      </main>
      <footer className="row-start-3 flex gap-[24px] flex-wrap items-center justify-center">
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4 text-gray-700 dark:text-gray-300"
          href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/file.svg"
            alt="File icon"
            width={16}
            height={16}
            className="dark:invert"
          />
          Learn
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4 text-gray-700 dark:text-gray-300"
          href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/window.svg"
            alt="Window icon"
            width={16}
            height={16}
            className="dark:invert"
          />
          Examples
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4 text-gray-700 dark:text-gray-300"
          href="https://nextjs.org?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/globe.svg"
            alt="Globe icon"
            width={16}
            height={16}
            className="dark:invert"
          />
          Go to nextjs.org →
        </a>
      </footer>
    </div>
  );
}
