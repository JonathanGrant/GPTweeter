let BASE_URL;

if (process.env.NODE_ENV === 'development') {
  BASE_URL = 'http://localhost:5000/api';
}  else {
  // BASE_URL = '/api';
  BASE_URL = 'https://weathergpt.us/api';
}

const getTweets = async (topic) => {
  try {
    const response = await fetch(`${BASE_URL}/tweets/${topic}`, {
      method: 'GET',
    });
    const json = await response.json();
    return json;
  } catch (error) {
    console.error(error);
    throw error;
  }
};

export default {
  getTweets,
};
