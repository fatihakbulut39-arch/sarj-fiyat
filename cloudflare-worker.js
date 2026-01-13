/**
 * Cloudflare Worker - Şarj Fiyatları API
 * Workers KV'den veri sunar
 * 
 * Deployment:
 * 1. npm init -y
 * 2. npm install wrangler --save-dev
 * 3. npx wrangler login
 * 4. npx wrangler deploy
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-API-Key',
      'Content-Type': 'application/json; charset=utf-8'
    };

    // Preflight request
    if (request.method === 'OPTIONS') {
      return new Response('', { headers: corsHeaders });
    }

    // GET /api/prices - Tüm fiyatları getir
    if (path === '/api/prices' && request.method === 'GET') {
      try {
        const prices = await env.PRICES_KV.get('charging_prices', 'json');
        
        if (!prices) {
          return new Response(
            JSON.stringify({
              error: 'No prices found',
              message: 'Veri henüz yüklenmedi. Lütfen sonra tekrar deneyin.'
            }),
            { 
              status: 404, 
              headers: corsHeaders 
            }
          );
        }

        return new Response(
          JSON.stringify({
            success: true,
            data: prices,
            count: prices.length,
            lastUpdated: await env.PRICES_KV.get('last_updated'),
            timestamp: new Date().toISOString()
          }),
          { 
            status: 200,
            headers: {
              ...corsHeaders,
              'Cache-Control': 'public, max-age=3600' // 1 saat cache
            }
          }
        );
      } catch (error) {
        return new Response(
          JSON.stringify({ error: error.message }),
          { status: 500, headers: corsHeaders }
        );
      }
    }

    // POST /api/update - Veriyi güncelle (API key gerekli)
    if (path === '/api/update' && request.method === 'POST') {
      try {
        // API Key kontrolü
        const apiKey = request.headers.get('X-API-Key');
        if (apiKey !== env.API_KEY) {
          return new Response(
            JSON.stringify({ error: 'Invalid API key' }),
            { status: 401, headers: corsHeaders }
          );
        }

        // Veriyi oku
        const data = await request.json();

        // Validasyon
        if (!Array.isArray(data)) {
          return new Response(
            JSON.stringify({ error: 'Data must be an array' }),
            { status: 400, headers: corsHeaders }
          );
        }

        // KV'ye kaydet
        await env.PRICES_KV.put('charging_prices', JSON.stringify(data));
        await env.PRICES_KV.put('last_updated', new Date().toISOString());

        return new Response(
          JSON.stringify({
            success: true,
            message: `${data.length} firma kaydedildi`,
            timestamp: new Date().toISOString()
          }),
          { status: 200, headers: corsHeaders }
        );
      } catch (error) {
        return new Response(
          JSON.stringify({ error: error.message }),
          { status: 500, headers: corsHeaders }
        );
      }
    }

    // GET / - Health check
    if (path === '/' && request.method === 'GET') {
      return new Response(
        JSON.stringify({
          status: 'ok',
          message: 'Şarj Fiyatları API',
          endpoints: {
            'GET /api/prices': 'Tüm fiyatları getir',
            'POST /api/update': 'Fiyatları güncelle (API key gerekli)',
            'GET /api/health': 'Health check'
          }
        }),
        { status: 200, headers: corsHeaders }
      );
    }

    // GET /api/health - Health check
    if (path === '/api/health' && request.method === 'GET') {
      try {
        const lastUpdated = await env.PRICES_KV.get('last_updated');
        const count = (await env.PRICES_KV.get('charging_prices', 'json'))?.length || 0;

        return new Response(
          JSON.stringify({
            status: 'healthy',
            dataCount: count,
            lastUpdated: lastUpdated,
            timestamp: new Date().toISOString()
          }),
          { status: 200, headers: corsHeaders }
        );
      } catch (error) {
        return new Response(
          JSON.stringify({ status: 'error', error: error.message }),
          { status: 500, headers: corsHeaders }
        );
      }
    }

    // 404
    return new Response(
      JSON.stringify({ error: 'Not found' }),
      { status: 404, headers: corsHeaders }
    );
  }
};
