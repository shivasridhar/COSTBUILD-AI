import React, { useState } from 'react';
import { predictOptimalBuildWindow } from './api/client';
import HealthBadge from './components/HealthBadge';
import InputForm from './components/InputForm';
import RecommendationCard from './components/RecommendationCard';
import ForecastChart from './components/ForecastChart';
import BomTable from './components/BomTable';
import AnchorConversionCard from './components/AnchorConversionCard';
import LimitationNotice from './components/LimitationNotice';
import { HardHat } from 'lucide-react';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [results, setResults] = useState(null);

  const handleFormSubmit = async (payload) => {
    setLoading(true);
    setApiError(null);

    try {
      const data = await predictOptimalBuildWindow(payload);
      setResults(data);
    } catch (err) {
      setResults(null);
      // Display actual error message returned from API response or network failure
      setApiError(err.message || 'An unexpected error occurred while contacting the API.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="brand-section">
          <div className="brand-icon">
            <HardHat size={26} />
          </div>
          <div>
            <h1 className="brand-title">BuildCost AI</h1>
            <p className="brand-tagline">Procurement Optimization & Dynamic BOM Trajectory Engine</p>
          </div>
        </div>
        <HealthBadge />
      </header>

      {/* Main Input Form */}
      <section className="input-section">
        <InputForm onSubmit={handleFormSubmit} loading={loading} apiError={apiError} />
      </section>

      {/* Results View - Only rendered when real API response is received */}
      {results && (
        <main className="results-section">
          {/* Strategic Recommendation */}
          <RecommendationCard recommendation={results.recommendation} />

          {/* 12-Month Price Trajectory Chart */}
          <ForecastChart forecastData={results.forecast} />

          {/* Monthly BOM Cost Breakdown Table */}
          <BomTable
            bomData={results.bom_cost_by_month}
            recommendedMonth={results.recommendation?.recommended_year_month}
          />

          {/* Anchor Conversion Summary with Sanity Check Badge */}
          <AnchorConversionCard anchorData={results.anchor_conversion} />

          {/* Honest Model Limitation Notice */}
          <LimitationNotice metadata={results.metadata} />
        </main>
      )}
    </div>
  );
}
