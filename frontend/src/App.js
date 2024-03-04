import React, { useEffect, useRef, useState } from "react";
import "./App.css";
import api from "./api";
import TextInputWithSubmit from "./TextInputWithSubmit"

import { Card, CardContent, Typography, Grid, CardMedia, Box, IconButton, CircularProgress, TextField, AppBar, Toolbar, Container, InputLabel } from '@mui/material';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import RepeatIcon from '@mui/icons-material/Repeat';


const getRandomInt = (max) => Math.floor(Math.random() * max);

function TweetDisplay({ tweet, index }) {
  return (
    <Grid item xs={12} key={index}>
      <Card sx={{ bgcolor: 'background.paper', color: 'text.primary' }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={2}>
              <CardMedia
                component="img"
                height="80"
                image={`https://cataas.com/cat?${new Date().getTime() + index}`}
                alt="Cat profile pic"
              />
            </Grid>
            <Grid item xs={10}>
              <Typography variant="h6" component="div" sx={{ color: 'primary.main' }}>
                {tweet.user_name} <span style={{ color: '#aaa', fontSize: '0.8rem' }}>{tweet.datetime}</span>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {tweet.text}
              </Typography>
            </Grid>
          </Grid>
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
            <IconButton aria-label="add to favorites" sx={{ color: 'error.main' }}>
              <FavoriteBorderIcon /> {getRandomInt(500)}
            </IconButton>
            <IconButton aria-label="retweet" sx={{ color: 'success.main' }}>
              <RepeatIcon /> {getRandomInt(100)}
            </IconButton>
          </Box>
        </CardContent>
      </Card>
    </Grid>
  );
}


function App() {
  const [topic, setTopic] = useState("random");
  const [tweets, setTweets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const loader = useRef(null);

  React.useEffect(()=> {
    if (loading) return
    setLoading(true);
    const getTweets = async (topic) => {
      let tweets = await api.getTweets(topic);
      console.log(tweets);
      setTweets(t => [...t, ...tweets["tweets"]]);
      setLoading(false);
    }
    getTweets(topic);
  }, [topic, page])

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !loading) {
        setPage((prevPage) => prevPage + 1);
      }
    });

    if (loader.current) {
      observer.observe(loader.current);
    }

    return () => {
      if (loader.current) {
        observer.unobserve(loader.current);
      }
    };
  }, [loading]);

  return (
    <div className="app">
      <AppBar>
      <TextInputWithSubmit onSubmit={setTopic} />
      </AppBar>
    <Box sx={{ bgcolor: 'background.default', color: 'text.primary', p: 3 }}>
      <Grid container spacing={2}>
        {tweets.map((tweet, index) => <TweetDisplay key={index} tweet={tweet} index={index} />)}
     </Grid>
     {loading ? (<Grid>
      <CircularProgress color="secondary" />
      <CircularProgress color="success" />
      <CircularProgress color="inherit" />
     </Grid>) : null}
     <div ref={loader} style={{ height: '100px', margin: '30px' }} />
    </Box>
    </div>
  );
}

export default App;