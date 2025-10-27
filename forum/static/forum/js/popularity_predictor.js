/**
 * Widget de prédiction de popularité en temps réel
 * À intégrer dans le formulaire de création de topic
 */

class PopularityPredictor {
    constructor(formSelector) {
        this.form = document.querySelector(formSelector);
        this.titleInput = this.form.querySelector('[name="title"]');
        this.contentInput = this.form.querySelector('[name="content"]');
        this.categoryInput = this.form.querySelector('[name="category"]');
        this.resultDiv = document.getElementById('popularity-prediction');
        
        this.debounceTimer = null;
        this.init();
    }
    
    init() {
        // Écouter les changements avec debounce
        this.titleInput.addEventListener('input', () => this.debouncedPredict());
        this.contentInput.addEventListener('input', () => this.debouncedPredict());
        this.categoryInput.addEventListener('change', () => this.predict());
    }
    
    debouncedPredict() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => this.predict(), 1000);
    }
    
    async predict() {
        const title = this.titleInput.value.trim();
        const content = this.contentInput.value.trim();
        const categoryId = this.categoryInput.value;
        
        // Validation minimale
        if (!title || !content || !categoryId) {
            this.resultDiv.innerHTML = '<div class="alert alert-info">Remplissez le formulaire pour voir la prédiction...</div>';
            return;
        }
        
        // Afficher loader
        this.resultDiv.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>Analyse en cours...</p></div>';
        
        try {
            const response = await fetch('/forum/api/predict-popularity/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    title: title,
                    content: content,
                    category_id: categoryId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayPrediction(data.prediction);
            } else {
                this.displayError(data.error);
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.displayError('Erreur lors de la prédiction');
        }
    }
    
    displayPrediction(prediction) {
        const scoreColor = this.getScoreColor(prediction.popularity_score);
        const icon = this.getScoreIcon(prediction.popularity_score);
        
        let html = `
            <div class="card shadow-sm border-${scoreColor}">
                <div class="card-header bg-${scoreColor} text-white">
                    <h5 class="mb-0">${icon} Prédiction de Popularité IA</h5>
                </div>
                <div class="card-body">
                    <div class="row text-center mb-3">
                        <div class="col-md-6">
                            <h6 class="text-muted">Vues prévues</h6>
                            <h3 class="text-primary">${prediction.predicted_views}</h3>
                        </div>
                        <div class="col-md-6">
                            <h6 class="text-muted">Réponses prévues</h6>
                            <h3 class="text-success">${prediction.predicted_posts}</h3>
                        </div>
                    </div>
                    
                    <div class="text-center mb-3">
                        <h4>${prediction.category}</h4>
                        <div class="progress" style="height: 25px;">
                            <div class="progress-bar bg-${scoreColor}" 
                                 role="progressbar" 
                                 style="width: ${prediction.popularity_score}%"
                                 aria-valuenow="${prediction.popularity_score}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100">
                                ${prediction.popularity_score}/100
                            </div>
                        </div>
                        <small class="text-muted">Confiance: ${prediction.confidence}</small>
                    </div>
        `;
        
        // Recommandations
        if (prediction.recommendations && prediction.recommendations.length > 0) {
            html += '<div class="alert alert-warning"><strong>💡 Recommandations:</strong><ul class="mb-0 mt-2">';
            prediction.recommendations.forEach(rec => {
                html += `<li>${rec}</li>`;
            });
            html += '</ul></div>';
        }
        
        html += '</div></div>';
        
        this.resultDiv.innerHTML = html;
    }
    
    displayError(message) {
        this.resultDiv.innerHTML = `<div class="alert alert-danger">${message}</div>`;
    }
    
    getScoreColor(score) {
        if (score >= 80) return 'danger';
        if (score >= 60) return 'success';
        if (score >= 40) return 'info';
        return 'secondary';
    }
    
    getScoreIcon(score) {
        if (score >= 80) return '🔥';
        if (score >= 60) return '⭐';
        if (score >= 40) return '📊';
        return '💤';
    }
    
    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}

// Initialiser quand le DOM est prêt
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form#topic-form');
    if (form) {
        new PopularityPredictor('form#topic-form');
    }
});
