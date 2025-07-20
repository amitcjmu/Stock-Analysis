// Debug component to test Checkbox behavior
import React from 'react';

export const DebugCheckbox = () => {
  const handleChange = (checked: boolean | unknown) => {
    console.log('Checkbox changed:', checked);
    console.log('Type of checked:', typeof checked);
    console.log('Is boolean?', typeof checked === 'boolean');
    
    // If checked is an object, this would cause the React child error
    if (typeof checked === 'object') {
      console.error('ERROR: Checkbox is passing an object instead of boolean!');
      console.error('Object keys:', Object.keys(checked));
      console.error('Object:', checked);
    }
  };

  return (
    <div>
      <h1>Debug Checkbox</h1>
      <p>Check console for output</p>
      {/* This would simulate the error if we try to render an object */}
      {/* {checked} */}
    </div>
  );
};