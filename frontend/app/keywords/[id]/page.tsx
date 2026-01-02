import { api, KeywordDetail, KeywordHistory } from '@/lib/api';
import { notFound } from 'next/navigation';
import KeywordDetailClient from '@/components/KeywordDetailClient';

async function getKeyword(id: number): Promise<KeywordDetail | null> {
  try {
    return await api.getKeyword(id);
  } catch (error) {
    console.error('Error fetching keyword:', error);
    return null;
  }
}

async function getKeywordHistory(id: number): Promise<KeywordHistory | null> {
  try {
    return await api.getKeywordHistory(id, 90); // Last 90 days
  } catch (error) {
    console.error('Error fetching history:', error);
    return null;
  }
}

export default async function KeywordDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const id = parseInt(params.id);
  
  if (isNaN(id)) {
    notFound();
  }

  const [keyword, history] = await Promise.all([
    getKeyword(id),
    getKeywordHistory(id),
  ]);

  if (!keyword) {
    notFound();
  }

  return (
    <main className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <KeywordDetailClient keyword={keyword} history={history} />
      </div>
    </main>
  );
}

