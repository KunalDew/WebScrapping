import NextAuth, { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username: { label: "Username", type: "text", placeholder: "testuser" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (
          credentials?.username === "testuser" &&
          credentials?.password === "password123"
        ) {
          return { id: "1", name: "Test User", email: "test@example.com" };
        }
        return null;
      }
    })
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        // Inject the backend API key from env into the JWT token on first login
        token.backendApiKey = process.env.BACKEND_API_KEY;
      }
      return token;
    },
    async session({ session, token }) {
      // Expose the backend API key to the client session
      session.backendApiKey = token.backendApiKey as string;
      return session;
    }
  },
  pages: {
    signIn: "/login",
  },
  secret: process.env.NEXTAUTH_SECRET,
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
