/** GitHub Actions secret names for Google OAuth / YouTube uploads. */

export const GCLOUD_CLIENT_ID_KEYS = [
  "GCLOUD_CLIENT_ID",
  "GCLOUD_AUTH_CLIENT_ID",
  "VIDGET_CLIENT_ID",
] as const;

export const GCLOUD_CLIENT_SECRET_KEYS = ["GCLOUD_CLIENT_SECRET", "VIDGET_CLIENT_SECRET"] as const;

export const GCLOUD_REFRESH_TOKEN_KEYS = ["GCLOUD_REFRESH_TOKEN", "VIDGET_REFRESH_TOKEN"] as const;

export const CANONICAL_CLIENT_ID_SECRET = "GCLOUD_CLIENT_ID";
export const CANONICAL_CLIENT_SECRET = "VIDGET_CLIENT_SECRET";
export const CANONICAL_REFRESH_TOKEN = "VIDGET_REFRESH_TOKEN";

export function hasAnySecret(names: readonly string[], existing: string[]): boolean {
  return names.some((n) => existing.includes(n));
}
