import http from 'k6/http';
import { Trend } from 'k6/metrics';
import { check } from 'k6';

const statusTrend = new Trend('status_codes');

export const options = {
    stages: [
        { duration: '10s', target: 100 },
        { duration: '20s', target: 100 },
        { duration: '10s', target: 0 },
    ],
    // Resolución explícita del host (equivalente a *.localhost -> 127.0.0.1)
    hosts: { 'universidad.localhost': '127.0.0.1' },
    // Traefik sirve un certificado propio en desarrollo
    insecureSkipTLSVerify: true,
};

// Host del monolito tras Traefik (regla Host(`universidad.localhost`))
const BASE_URL = 'https://universidad.localhost';

// open() con modo 'b' devuelve un ArrayBuffer; la ruta es relativa a este script
const pdfFile = open('./data/simple.pdf', 'b');

export default function () {
    // El servicio rechaza checksums duplicados con 400 (is_duplicate en PDFService).
    // Se añade un sufijo único por iteración tras el %%EOF (pypdf lo tolera) para que
    // cada petición ejercite el camino completo de inserción (201) y no el de duplicados.
    // Nota: http.file solo acepta string o ArrayBuffer, por eso se usa merged.buffer.
    const pdfBytes = new Uint8Array(pdfFile);
    const suffix = new TextEncoder().encode(`k6-${__VU}-${__ITER}-${Date.now()}`);
    const merged = new Uint8Array(pdfBytes.length + suffix.length);
    merged.set(pdfBytes, 0);
    merged.set(suffix, pdfBytes.length);

    // El endpoint del monolito es POST /api/v1/upload y espera multipart/form-data
    const res = http.post(`${BASE_URL}/api/v1/upload`, {
        file: http.file(merged.buffer, 'simple.pdf', 'application/pdf'),
    });

    statusTrend.add(res.status);

    check(res, {
        'status 201': (r) => r.status === 201,
    });
}
