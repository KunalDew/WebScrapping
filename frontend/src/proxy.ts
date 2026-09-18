import { withAuth } from "next-auth/middleware";

const authMiddleware = withAuth({
  pages: {
    signIn: "/login",
  },
});

export default function proxy(req: any, ev: any) {
  return authMiddleware(req, ev);
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api/auth (NextAuth API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico, .svg (public files)
     * - login (the login page itself)
     */
    "/((?!api/auth|_next/static|_next/image|favicon.ico|.*\\.svg|login).*)",
  ],
};
