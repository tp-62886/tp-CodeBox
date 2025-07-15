from django import forms

class RecommendationForm(forms.Form):
    RECOMMENDATION_CHOICES = [
        ('1', '根据用户ID推荐工作'),
        ('2', '根据工作ID推荐用户'),
    ]
    recommendation_type = forms.ChoiceField(choices=RECOMMENDATION_CHOICES, label='推荐方向')
    input_id = forms.CharField(label='输入ID')
