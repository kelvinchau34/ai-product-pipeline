function BeforeAfterPreview({ beforeTitle, afterTitle, beforeContent, afterContent }) {
  return (
    <section className="drawer-section">
      <h3>Before / After</h3>
      <div className="compare-grid">
        <div className="compare-card">
          <span className="compare-label">{beforeTitle}</span>
          <p className="compare-text">{beforeContent || 'No vendor info available.'}</p>
        </div>
        <div className="compare-card">
          <span className="compare-label">{afterTitle}</span>
          {afterContent ? (
            <div
              className="compare-html"
              // eslint-disable-next-line react/no-danger
              dangerouslySetInnerHTML={{ __html: afterContent }}
            />
          ) : (
            <p className="compare-text">No Shopify info available.</p>
          )}
        </div>
      </div>
    </section>
  );
}

export default BeforeAfterPreview;
