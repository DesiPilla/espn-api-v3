import React from 'react';
import PropTypes from 'prop-types';

/**
 * A reusable component that displays a notification when data is not yet finalized
 * 
 * @param {Object} props
 * @param {string} props.dataType - The type of data that is likely to change (e.g., "playoff odds", "Power Rankings")
 * @param {boolean} props.isPending - Whether to display the notice or not
 */
const PendingDataNotice = ({ dataType, isPending }) => {
  if (!isPending) return null;
  
  return (
    <p className="pending-data-notice">
      <em>
        Note that scores have not yet been finalized for this
        week and the {dataType} {dataType.toLowerCase().includes('list') ? 'are' : 'is'} likely to change.
        <br />
        Please check back on Tuesday morning for the final
        results.
      </em>
    </p>
  );
};

PendingDataNotice.propTypes = {
  dataType: PropTypes.string.isRequired,
  isPending: PropTypes.bool.isRequired
};

export default PendingDataNotice;