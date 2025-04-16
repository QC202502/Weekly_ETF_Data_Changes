from flask import Blueprint, render_template
from database.models import get_etf_holder_recommendations, get_etf_price_recommendations, get_etf_attention_recommendations

recommendation_bp = Blueprint('recommendation', __name__)

@recommendation_bp.route('/recommendation_new')
def recommendation_new():
    """
    显示新版ETF推荐页面
    """
    holder_value_recommendations = get_etf_holder_recommendations()
    price_recommendations = get_etf_price_recommendations()
    attention_recommendations = get_etf_attention_recommendations()
    
    return render_template(
        'recommendation_new.html',
        holder_value_recommendations=holder_value_recommendations,
        price_recommendations=price_recommendations,
        attention_recommendations=attention_recommendations
    ) 