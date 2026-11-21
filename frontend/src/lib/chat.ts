// TODO: replace with a call to the backend chat endpoint once it exists
// (e.g. POST /api/chat). The Vercel/nginx config already proxies /api/*.
export async function sendMessage(text: string): Promise<string> {
  void text
  await new Promise((resolve) => setTimeout(resolve, 900))
  return 'This is a placeholder response. The chat endpoint is not connected yet.'
}
