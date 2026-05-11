function BeforeAfterPreview({ beforeTitle, afterTitle, beforeContent, afterContent }) {
  return (
    <section className="drawer-section">
      <h3>Before / After</h3>
      <div className="compare-grid">
        <div className="compare-card">
          <span className="compare-label">{beforeTitle}</span>
          <pre>{beforeContent || 'No vendor info available.'}</pre>
        </div>
        <div className="compare-card">
          <span className="compare-label">{afterTitle}</span>
          <pre>{afterContent || 'No Shopify info available.'}</pre>
        </div>
      </div>
    </section>
  );
}

export default BeforeAfterPreview;
