import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <Card className="max-w-md text-center">
        <h1 className="text-2xl font-semibold">Page not found</h1>
        <p className="mt-2 text-sm text-muted-foreground">The route you requested does not exist.</p>
        <Button asChild className="mt-4">
          <Link to="/">Back to home</Link>
        </Button>
      </Card>
    </div>
  )
}
