import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AI Doc Assistant - Chatbot RAG avec Claude',
  description: 'Assistant conversationnel utilisant RAG et Claude (Anthropic) pour répondre avec précision en se basant sur vos documents.',
  keywords: ['RAG', 'Claude', 'Anthropic', 'Chatbot', 'AI', 'LLM', 'Python', 'FastAPI'],
  authors: [{ name: 'Glody KUTUMBAKANA' }],
  openGraph: {
    title: 'AI Doc Assistant - Chatbot RAG avec Claude',
    description: 'Assistant conversationnel utilisant RAG et Claude (Anthropic)',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body className={inter.className}>{children}</body>
    </html>
  );
}