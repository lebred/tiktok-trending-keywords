import KeywordDetailClientPage from './KeywordDetailClientPage';

// MVP: pre-generate a fixed number of keyword pages.
// Increase/decrease depending on how many keyword IDs you expect.
const MAX_EXPORTED_KEYWORD_PAGES = 500;

export async function generateStaticParams() {
  // Generates: /keywords/1/ ... /keywords/500/
  return Array.from({ length: MAX_EXPORTED_KEYWORD_PAGES }, (_, i) => ({
    id: String(i + 1),
  }));
}

export default function KeywordDetailPage({ params }: { params: { id: string } }) {
  const idNum = Number(params.id);

  // Even though this is statically generated, keep a guard.
  // If someone requests a bad page, they'll just see the client error UI.
  return <KeywordDetailClientPage id={Number.isFinite(idNum) ? idNum : NaN} />;
}
