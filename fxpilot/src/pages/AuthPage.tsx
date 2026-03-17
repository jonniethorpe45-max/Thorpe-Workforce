import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { z } from 'zod'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAuth } from '@/providers/AuthProvider'

const authSchema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'Minimum 8 characters'),
})

type AuthFormValues = z.infer<typeof authSchema>

export function AuthPage() {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const { user, signInWithPassword, signUpWithPassword } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? '/dashboard'

  const form = useForm<AuthFormValues>({
    resolver: zodResolver(authSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  })

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  async function submit(values: AuthFormValues) {
    try {
      if (mode === 'login') {
        await signInWithPassword(values.email, values.password)
        toast.success('Welcome back to FXPilot.')
        void navigate(from, { replace: true })
      } else {
        await signUpWithPassword(values.email, values.password)
        toast.success('Account created. Please verify your email before logging in.')
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Authentication failed')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md">
        <h1 className="text-2xl font-semibold text-foreground">FXPilot Auth</h1>
        <p className="mt-2 text-sm text-muted-foreground">Email verification is required before live access.</p>

        <Tabs value={mode} onValueChange={(v) => setMode(v as 'login' | 'signup')} className="mt-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="login">Login</TabsTrigger>
            <TabsTrigger value="signup">Sign up</TabsTrigger>
          </TabsList>
          <TabsContent value={mode}>
            <form className="mt-4 space-y-4" onSubmit={form.handleSubmit(submit)}>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" {...form.register('email')} />
                <p className="text-xs text-danger">{form.formState.errors.email?.message}</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" {...form.register('password')} />
                <p className="text-xs text-danger">{form.formState.errors.password?.message}</p>
              </div>
              <Button className="w-full" type="submit" disabled={form.formState.isSubmitting}>
                {mode === 'login' ? 'Login to FXPilot' : 'Create account'}
              </Button>
            </form>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  )
}
