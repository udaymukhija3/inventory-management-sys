from app.services.velocity_analyzer import VelocityAnalyzer

def test_velocity_analyzer_initialization():
    analyzer = VelocityAnalyzer()
    assert analyzer is not None
