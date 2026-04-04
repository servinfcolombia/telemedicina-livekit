import { NextAuthOptions } from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'
import { JWT } from 'next-auth/jwt'

declare module 'next-auth/jwt' {
  interface JWT {
    accessToken?: string
  }
}

declare module 'next-auth' {
  interface Session {
    accessToken?: string
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      id: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email', placeholder: 'doctor@test.com' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        console.log('Authorize called with:', credentials)

        if (!credentials?.email || !credentials?.password) {
          console.log('Missing credentials')
          return null
        }

        try {
          const formData = new URLSearchParams()
          formData.append('username', credentials.email)
          formData.append('password', credentials.password)

          console.log('Sending to backend:', process.env.NEXT_PUBLIC_API_URL + '/api/v1/auth/login')
          console.log('Form data:', formData.toString())

          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData.toString(),
          })

          console.log('Backend response status:', response.status)

          if (!response.ok) {
            const errorText = await response.text()
            console.log('Backend error:', errorText)
            throw new Error(errorText)
          }

          const data = await response.json()
          console.log('Backend data:', JSON.stringify(data).substring(0, 200))

          if (data.access_token) {
            console.log('Got access_token, returning user')
            return {
              id: '1',
              email: credentials.email,
              name: credentials.email.split('@')[0],
              accessToken: data.access_token,
            }
          }

          console.log('No access_token in response')
          return null
        } catch (error) {
          console.error('Auth error:', error)
          throw error
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      console.log('JWT callback - user:', user)
      console.log('JWT callback - token before:', token)
      if (user) {
        token.id = user.id
        token.accessToken = (user as any).accessToken
        const at = token.accessToken as string
        console.log('JWT callback - added accessToken:', at?.substring(0, 20))
      }
      console.log('JWT callback - token after:', token)
      return token
    },
    async session({ session, token }) {
      console.log('Session callback - token:', token)
      const at = token.accessToken as string
      console.log('Session callback - accessToken in token:', at?.substring(0, 20))
      if (session.user) {
        (session.user as any).id = token.id
      }
      // Also put at root level
      ;(session as any).accessToken = token.accessToken
      return session
    },
  },
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  session: {
    strategy: 'jwt',
    maxAge: 15 * 60,
  },
  secret: process.env.NEXTAUTH_SECRET,
  debug: true,
}
