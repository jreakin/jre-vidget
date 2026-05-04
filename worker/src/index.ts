/**
 * vidget-auth — GitHub OAuth proxy for Cloudflare Workers
 *
 * Handles the OAuth callback so the browser never needs to call GitHub's
 * token exchange endpoint directly (which blocks CORS).
 *
 * Flow:
 *   Browser → GitHub authorize → GitHub redirects to /callback?code=XXX
 *   Worker exchanges code → access_token
 *   Worker redirects to ALLOWED_ORIGIN/#access_token=XXX
 */

export interface Env {
  GITHUB_CLIENT_ID: string;
  GITHUB_CLIENT_SECRET: string;
  ALLOWED_ORIGIN: string; // e.g. https://jreakin.github.io/jre-vidget
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders(env.ALLOWED_ORIGIN) });
    }

    // Health check
    if (url.pathname === "/health") {
      return json({ ok: true }, env.ALLOWED_ORIGIN);
    }

    // OAuth callback — exchange code for token, redirect to web UI
    if (url.pathname === "/callback") {
      const code = url.searchParams.get("code");
      if (!code) {
        return error("Missing code parameter", 400, env.ALLOWED_ORIGIN);
      }

      const tokenRes = await fetch("https://github.com/login/oauth/access_token", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          client_id: env.GITHUB_CLIENT_ID,
          client_secret: env.GITHUB_CLIENT_SECRET,
          code,
        }),
      });

      if (!tokenRes.ok) {
        return error("GitHub token exchange failed", 502, env.ALLOWED_ORIGIN);
      }

      const data = (await tokenRes.json()) as Record<string, string>;

      if (data.error) {
        return error(data.error_description ?? data.error, 400, env.ALLOWED_ORIGIN);
      }

      const token = data.access_token;
      const scope = data.scope ?? "";

      // Redirect to web UI with token in URL fragment (never hits server logs)
      const redirectUrl = `${env.ALLOWED_ORIGIN}/#access_token=${token}&scope=${encodeURIComponent(scope)}`;
      return Response.redirect(redirectUrl, 302);
    }

    // Token exchange for SPAs that can't do a redirect flow
    // POST /token  { code: "..." }  → { access_token, scope }
    if (url.pathname === "/token" && request.method === "POST") {
      let body: { code?: string };
      try {
        body = (await request.json()) as { code?: string };
      } catch {
        return error("Invalid JSON body", 400, env.ALLOWED_ORIGIN);
      }

      if (!body.code) {
        return error("Missing code in body", 400, env.ALLOWED_ORIGIN);
      }

      const tokenRes = await fetch("https://github.com/login/oauth/access_token", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          client_id: env.GITHUB_CLIENT_ID,
          client_secret: env.GITHUB_CLIENT_SECRET,
          code: body.code,
        }),
      });

      if (!tokenRes.ok) {
        return error("GitHub token exchange failed", 502, env.ALLOWED_ORIGIN);
      }

      const data = (await tokenRes.json()) as Record<string, string>;

      if (data.error) {
        return error(data.error_description ?? data.error, 400, env.ALLOWED_ORIGIN);
      }

      return json(
        { access_token: data.access_token, scope: data.scope },
        env.ALLOWED_ORIGIN,
      );
    }

    return error("Not found", 404, env.ALLOWED_ORIGIN);
  },
};

// --- helpers -----------------------------------------------------------------

function corsHeaders(origin: string): HeadersInit {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
  };
}

function json(body: unknown, origin: string, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...corsHeaders(origin),
    },
  });
}

function error(message: string, status: number, origin: string): Response {
  return json({ error: message }, origin, status);
}
