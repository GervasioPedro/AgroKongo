import { AuthProvider } from '../hooks/useAuth';
import '../styles/globals.css'; // Supondo que você tenha um ficheiro de estilos globais

function MyApp({ Component, pageProps }) {
  return (
    <AuthProvider>
      <Component {...pageProps} />
    </AuthProvider>
  );
}

export default MyApp;
