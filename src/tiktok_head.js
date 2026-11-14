'use strict';
/* Merci Studio – TikTok (9:16) version. Shared drawing code lives in _shared.js. */
const W = 1080, H = 1920, FPS = 30, DURATION = 59;
const PI = Math.PI, TAU = Math.PI * 2;
const cv = document.getElementById('c');
const mainCtx = cv.getContext('2d');
let g = mainCtx;
const IMG = {};
const C = {
  ink: '#272b38', yellow: '#ffc83d', green: '#58d26a', navy: '#1d2230', coral: '#ff7b86',
  blush: 'rgba(255,120,145,0.40)', shirt: '#2c2f3b', wall: '#f5ede3', wall2: '#eadccb',
  floor: '#b78962', floor2: '#946a49', paper: '#f6d6cf',
};
const FONT = 'Montserrat';
const F = (w, s) => `${w} ${s}px ${FONT}, sans-serif`;
