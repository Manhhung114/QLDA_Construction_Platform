import './globals.css';

export const metadata = {
  title: 'QLDA Construction Platform',
  description: 'Construction Project Management Platform'
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="vi"><body>{children}</body></html>;
}
