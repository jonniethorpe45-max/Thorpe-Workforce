import { Info } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

export function PwaInstallHelpDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button size="lg" variant="ghost">
          <Info className="mr-2 h-4 w-4" />
          Install Help
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>Install FXPilot</DialogTitle>
        <DialogDescription>
          Use these steps to install FXPilot as an app from your browser.
        </DialogDescription>

        <div className="space-y-4 text-sm">
          <section>
            <h3 className="font-semibold text-foreground">Desktop (Chrome / Edge)</h3>
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-muted-foreground">
              <li>Open FXPilot in the browser.</li>
              <li>Click <span className="font-medium text-foreground">Install App</span> on the landing page, or use the browser install icon in the address bar.</li>
              <li>Confirm install to launch FXPilot in standalone mode.</li>
            </ol>
          </section>

          <section>
            <h3 className="font-semibold text-foreground">Android (Chrome)</h3>
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-muted-foreground">
              <li>Open FXPilot in Chrome.</li>
              <li>Tap <span className="font-medium text-foreground">Install App</span> when shown, or open browser menu and tap <span className="font-medium text-foreground">Install app</span>.</li>
              <li>Confirm to add FXPilot to home screen.</li>
            </ol>
          </section>

          <section>
            <h3 className="font-semibold text-foreground">iPhone / iPad (Safari)</h3>
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-muted-foreground">
              <li>Open FXPilot in Safari.</li>
              <li>Tap the <span className="font-medium text-foreground">Share</span> button.</li>
              <li>Choose <span className="font-medium text-foreground">Add to Home Screen</span>, then tap <span className="font-medium text-foreground">Add</span>.</li>
            </ol>
          </section>
        </div>
      </DialogContent>
    </Dialog>
  )
}
