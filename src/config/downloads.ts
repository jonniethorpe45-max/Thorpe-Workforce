/** Public releases page — prefer runtime links from getReleaseDownloads(). */
export const THORPE_RELEASES_PAGE =
  "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest";

/** @deprecated Use thorpeApi.getReleaseDownloads() for installer URLs. */
export const THORPE_DOWNLOADS = {
  releasesPage: THORPE_RELEASES_PAGE,
} as const;
