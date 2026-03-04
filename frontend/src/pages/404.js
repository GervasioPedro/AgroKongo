// src/pages/404.js
import Link from 'next/link';

export default function Custom404() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      textAlign: 'center',
      fontFamily: 'sans-serif',
      backgroundColor: '#f9f9f9',
      color: '#333'
    }}>
      <h1 style={{ fontSize: '10rem', margin: 0, fontWeight: 'bold' }}>404</h1>
      <h2 style={{ fontSize: '2rem', margin: '0 0 1rem 0' }}>Página Não Encontrada</h2>
      <p style={{ maxWidth: '400px', marginBottom: '2rem' }}>
        Lamentamos, mas a página que você está a procurar não existe, foi removida ou está temporariamente indisponível.
      </p>
      <Link href="/" style={{
        padding: '1rem 2rem',
        backgroundColor: '#0070f3',
        color: 'white',
        textDecoration: 'none',
        borderRadius: '5px',
        fontWeight: 'bold'
      }}>
        Voltar à Página Inicial
      </Link>
    </div>
  );
}
