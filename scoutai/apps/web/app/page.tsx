import Link from 'next/link';

export default function HomePage() {
  return (
    <main>
      <div className="card">
        <p className="brand">ScoutAI</p>
        <p className="subtitle">
          Foundation for a sports recruiting intelligence platform. Stage 3 provides auth,
          API health checks, and background job infrastructure — not the full athlete product
          surface.
        </p>
        <div className="actions">
          <Link className="button buttonPrimary" href="/sign-in">
            Sign in
          </Link>
          <Link className="button buttonSecondary" href="/register">
            Register
          </Link>
        </div>
      </div>
      <p className="footerNote">
        API requests from the browser use <code>credentials: &apos;include&apos;</code> so
        session cookies issued by the API are sent on cross-origin calls. The API must enable
        CORS with <code>credentials: true</code> and allow <code>http://localhost:3000</code>{' '}
        (see <code>CORS_ORIGIN</code> in the API environment).
      </p>
    </main>
  );
}
