// static/js/calendario.js

// Configuração do calendário Flatpickr
let checkinPicker = null;
let checkoutPicker = null;

// Função para carregar datas ocupadas do servidor
async function carregarDatasOcupadas(quarto) {
    if (!quarto) return [];
    try {
        const response = await fetch(`/api/datas-ocupadas?quarto=${quarto}`);
        const data = await response.json();
        return data.datas || [];
    } catch (error) {
        console.error('Erro ao carregar datas ocupadas:', error);
        return [];
    }
}

// Calcular número de noites
function calcularNoites(data1, data2) {
    if (!data1 || !data2) return 0;
    const d1 = new Date(data1);
    const d2 = new Date(data2);
    const diffTime = Math.abs(d2 - d1);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
}

// Obter preço do quarto baseado no texto da option
function getPrecoQuarto() {
    const select = document.getElementById('quarto');
    if (!select || !select.value) return 450;
    
    const option = select.options[select.selectedIndex];
    const texto = option.text;
    const match = texto.match(/R\$ (\d+)/);
    return match ? parseInt(match[1]) : 450;
}

// Obter nome do quarto
function getNomeQuarto() {
    const select = document.getElementById('quarto');
    if (!select || !select.value) return '-';
    return select.options[select.selectedIndex].text.split(' - ')[0];
}

// Atualizar resumo da reserva
async function atualizarResumo() {
    const checkin = document.getElementById('checkin')?.value;
    const checkout = document.getElementById('checkout')?.value;
    const quartoSelect = document.getElementById('quarto');
    const camaextraCheck = document.getElementById('camaextra');
    
    if (!quartoSelect || !quartoSelect.value) return;
    
    const precoDiaria = getPrecoQuarto();
    const camaextra = camaextraCheck ? camaextraCheck.checked : false;
    
    if (checkin && checkout && quartoSelect.value) {
        const noites = calcularNoites(checkin, checkout);
        let valorTotal = precoDiaria * noites;
        if (camaextra) valorTotal += 50 * noites;
        
        document.getElementById('resumoQuarto').innerText = getNomeQuarto();
        document.getElementById('resumoCheckin').innerText = formatarDataBR(checkin);
        document.getElementById('resumoCheckout').innerText = formatarDataBR(checkout);
        document.getElementById('resumoNoites').innerText = noites;
        document.getElementById('resumoValor').innerHTML = `R$ ${valorTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
        document.getElementById('resumoReserva').style.display = 'block';
    } else {
        const resumoDiv = document.getElementById('resumoReserva');
        if (resumoDiv) resumoDiv.style.display = 'none';
    }
}

// Formatar data para exibição
function formatarDataBR(dataString) {
    const data = new Date(dataString);
    return data.toLocaleDateString('pt-BR');
}

// Inicializar calendários
async function inicializarCalendarios() {
    const quartoSelect = document.getElementById('quarto');
    if (!quartoSelect) return;
    
    const quarto = quartoSelect.value;
    if (!quarto) return;
    
    // Carregar datas ocupadas
    const datasBloqueadas = await carregarDatasOcupadas(quarto);
    
    // Destruir pickers existentes se houver
    if (checkinPicker) checkinPicker.destroy();
    if (checkoutPicker) checkoutPicker.destroy();
    
    // Configurar Check-in
    const checkinInput = document.getElementById('checkin');
    if (checkinInput) {
        checkinPicker = flatpickr(checkinInput, {
            locale: "pt",
            dateFormat: "Y-m-d",
            minDate: "today",
            disable: datasBloqueadas,
            onChange: function(selectedDates, dateStr, instance) {
                if (checkoutPicker) {
                    checkoutPicker.set('minDate', dateStr);
                }
                const checkoutInput = document.getElementById('checkout');
                if (checkoutInput && checkoutInput.value && 
                    new Date(checkoutInput.value) <= new Date(dateStr)) {
                    checkoutInput.value = '';
                    if (checkoutPicker) checkoutPicker.setDate(null);
                }
                atualizarResumo();
            }
        });
    }
    
    // Configurar Check-out
    const checkoutInput = document.getElementById('checkout');
    if (checkoutInput) {
        checkoutPicker = flatpickr(checkoutInput, {
            locale: "pt",
            dateFormat: "Y-m-d",
            minDate: "today",
            disable: datasBloqueadas,
            onChange: function() {
                atualizarResumo();
            }
        });
    }
}

// Verificar disponibilidade em tempo real
async function verificarDisponibilidade() {
    const quarto = document.getElementById('quarto')?.value;
    const checkin = document.getElementById('checkin')?.value;
    const checkout = document.getElementById('checkout')?.value;
    
    if (!quarto || !checkin || !checkout) return true;
    
    try {
        const response = await fetch(`/api/verificar-disponibilidade?quarto=${quarto}&entrada=${checkin}&saida=${checkout}`);
        const data = await response.json();
        
        if (!data.disponivel) {
            alert(`❌ Quarto não disponível para o período selecionado!\nDatas ocupadas: ${data.motivo || 'já reservado'}`);
            return false;
        }
        return true;
    } catch (error) {
        console.error('Erro ao verificar disponibilidade:', error);
        return true;
    }
}

// Envio do formulário
async function enviarReserva(form) {
    const formData = new FormData(form);
    const msgSpan = document.getElementById('reserveMsg');
    
    // Verificar disponibilidade antes de enviar
    const disponivel = await verificarDisponibilidade();
    if (!disponivel) return false;
    
    try {
        const response = await fetch('/reservas/nova', {
            method: 'POST',
            body: formData
        });
        
        if (response.redirected) {
            if (msgSpan) {
                msgSpan.innerHTML = '🌿 Reserva realizada com sucesso! Redirecionando...';
                msgSpan.style.color = '#2C5F2D';
            }
            setTimeout(() => {
                window.location.href = response.url;
            }, 1500);
            return true;
        } else {
            const result = await response.json();
            if (result.error) {
                if (msgSpan) {
                    msgSpan.innerHTML = '❌ ' + result.error;
                    msgSpan.style.color = '#dc3545';
                }
            }
            return false;
        }
    } catch (error) {
        if (msgSpan) {
            msgSpan.innerHTML = '❌ Erro ao processar reserva. Tente novamente.';
            msgSpan.style.color = '#dc3545';
        }
        return false;
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar calendários
    inicializarCalendarios();
    
    // Adicionar listeners
    const quartoSelect = document.getElementById('quarto');
    if (quartoSelect) {
        quartoSelect.addEventListener('change', function() {
            inicializarCalendarios();
            atualizarResumo();
        });
    }
    
    const camaextraCheck = document.getElementById('camaextra');
    if (camaextraCheck) {
        camaextraCheck.addEventListener('change', atualizarResumo);
    }
    
    // Configurar envio do formulário
    const form = document.getElementById('bookingVitta');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await enviarReserva(form);
            
            // Limpar mensagem após 5 segundos
            setTimeout(() => {
                const msgSpan = document.getElementById('reserveMsg');
                if (msgSpan) msgSpan.innerHTML = '';
            }, 5000);
        });
    }
});