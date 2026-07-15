import Link from 'next/link';

export default function UnauthorizedPage() {
  return (
    <main>
      <div className="card">
        <h1>Unauthorized</h1>
        <p>You are signed in but do not have permission to view this resource.</p>
        <div className="actions">
          <Link className="button buttonPrimary" href="/app">
            Back to dashboard
          </Link>
          <Link className="button buttonSecondary" href="/sign-in">
            Sign in as another user
          </Link>
        </div>
      </div>
    </main>
  );
}
