import React, { useState } from 'react';

// The 'onSubmit' function is expected to be passed via props
function TextInputWithSubmit({ onSubmit }) {
  // State to hold the input value
  const [inputValue, setInputValue] = useState('');

  // Handle input change
  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault(); // Prevent default form submission behavior
    if(onSubmit && typeof onSubmit === 'function') {
      onSubmit(inputValue); // Call the passed-in function with the current input value
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ width: '100%' }}>
      <input
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        style={{ width: '100%' }} // Full-width text box
      />
      <button type="submit">Submit</button>
    </form>
  );
}

export default TextInputWithSubmit;
