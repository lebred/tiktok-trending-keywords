// Required for static export with dynamic routes
export async function generateStaticParams() {
  // Return empty array - pages will be handled client-side
  // This allows static export to work without pre-generating all keyword pages
  return [];
}

