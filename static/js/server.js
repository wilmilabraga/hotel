const express = require('express');
const app = express();
const PORT = 3000;

app.use(express.urlencoded({ extended: true }));
app.use(express.static('public')); // Coloque seu HTML na pasta 'public'

// Endpoint para datas ocupadas
app.get('/api/datas-ocupadas', (req, res) => {
    const { quarto } = req.query;
    // Aqui você consultaria um banco de dados
    res.json({ datas: [] }); // Retorna array vazio por enquanto
});

// Endpoint para reservas
app.post('/reservas/nova', (req, res) => {
    console.log('Reserva recebida:', req.body);
    res.redirect('/obrigado.html'); // Redireciona para página de confirmação
});

app.listen(PORT, () => {
    console.log(`Servidor rodando em http://localhost:${PORT}`);
});