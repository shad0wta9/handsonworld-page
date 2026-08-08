const comparisons={
 dataset:{count:3,base:'static/videos/dataset'},
 method:{count:5,base:'static/videos/method'},
 ood:{count:4,base:'static/videos/ood'}
};

const fmt=s=>`${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`;

function bindVideoOverlay(main,control){
 const sync=()=>{
  if(Number.isFinite(main.currentTime)&&Math.abs(control.currentTime-main.currentTime)>.08){
   control.currentTime=main.currentTime;
  }
  control.playbackRate=main.playbackRate;
 };
 main.addEventListener('play',()=>{sync();control.play().catch(()=>{})});
 main.addEventListener('pause',()=>control.pause());
 main.addEventListener('seeking',sync);
 main.addEventListener('seeked',sync);
 main.addEventListener('ratechange',sync);
 main.addEventListener('timeupdate',sync);
 main.addEventListener('ended',()=>{control.pause();control.currentTime=0});
 control.addEventListener('loadedmetadata',sync);
 if(!main.paused)control.play().catch(()=>{});
}

function setupTeaser(){
 const main=document.querySelector('#teaser-main');
 const control=document.querySelector('#teaser-control');
 const toggle=document.querySelector('#show-control');
 if(!main||!control||!toggle)return;
 bindVideoOverlay(main,control);
 toggle.addEventListener('change',()=>control.classList.toggle('is-hidden',!toggle.checked));
}

function setupInteractionControls(){
 const players=[...document.querySelectorAll('.showcase-video-player')];
 if(!players.length)return;
 players.forEach(player=>{
  const main=player.querySelector('.interaction-main');
  const control=player.querySelector('.interaction-control');
  bindVideoOverlay(main,control);
 });
 document.querySelectorAll('.showcase-control-toggle input').forEach(toggle=>{
  toggle.addEventListener('change',()=>{
   toggle.closest('.showcase-column').querySelectorAll('.interaction-control')
    .forEach(control=>control.classList.toggle('is-hidden',!toggle.checked));
  });
 });
}

function setupAnnotationCarousel(){
 const root=document.querySelector('.annotation-carousel');
 if(!root)return;
 const stage=root.querySelector('.annotation-stage');
 const video=stage.querySelector('video');
 const counter=root.querySelector('.annotation-counter');
 const cases=Array.from({length:9},(_,i)=>
  `static/videos/annotations/case${String(i+1).padStart(2,'0')}.mp4`);
 let index=0;

 const show=(next,direction)=>{
  if(next===index)return;
  stage.classList.add(direction==='prev'?'is-switching-prev':'is-switching-next');
  window.setTimeout(()=>{
   index=(next+cases.length)%cases.length;
   video.src=cases[index];
   video.load();
   counter.textContent=`${String(index+1).padStart(2,'0')} / ${String(cases.length).padStart(2,'0')}`;
   video.addEventListener('loadeddata',()=>{
    stage.classList.remove('is-switching-prev','is-switching-next');
    video.play().catch(()=>{});
   },{once:true});
  },180);
 };
 root.querySelector('.annotation-prev').addEventListener('click',()=>show(index-1,'prev'));
 root.querySelector('.annotation-next').addEventListener('click',()=>show(index+1,'next'));
}

function setupComparison(id){
 const root=document.querySelector(`[data-comparison="${id}"]`),config=comparisons[id];
 const caseList=root.querySelector('.cases');
 if(id==='method'){
  ['EgoVid-Pro - 01','EgoVid-Pro - 02','EgoVid-Pro - 03'].forEach((label,index)=>{
   const button=document.createElement('button');button.className='case';
   button.innerHTML=`<img src="static/thumbs/method${index+3}.jpg" alt="${label}"><span>${label}</span>`;
   caseList.appendChild(button);
  });
 }
 const videos=[...root.querySelectorAll('video')],play=root.querySelector('.play'),range=root.querySelector('.range'),time=root.querySelector('.time');
 const buttons=[...root.querySelectorAll('.case')];let dragging=false;
 function loadCase(index){
  videos.forEach((video,i)=>{video.pause();video.src=`${config.base}/case${index+1}/m${i+1}.mp4`;video.load()});
  buttons.forEach((button,i)=>button.classList.toggle('active',i===index));play.textContent='▶';range.value=0;time.textContent='0:00 / 0:00';
 }
 play.addEventListener('click',()=>{const playing=!videos[0].paused;if(playing){videos.forEach(v=>v.pause());play.textContent='▶'}else{const t=videos[0].currentTime;videos.forEach(v=>{v.currentTime=t;v.play()});play.textContent='❚❚'}});
 videos[0].addEventListener('loadedmetadata',()=>time.textContent=`0:00 / ${fmt(videos[0].duration)}`);
 videos[0].addEventListener('timeupdate',()=>{if(dragging)return;range.value=videos[0].duration?videos[0].currentTime/videos[0].duration*100:0;time.textContent=`${fmt(videos[0].currentTime)} / ${fmt(videos[0].duration||0)}`;videos.slice(1).forEach(v=>{if(Math.abs(v.currentTime-videos[0].currentTime)>.12)v.currentTime=videos[0].currentTime})});
 videos[0].addEventListener('ended',()=>{play.textContent='▶';videos.forEach(v=>{v.pause();v.currentTime=0})});
 range.addEventListener('input',()=>{dragging=true;const t=videos[0].duration*range.value/100;videos.forEach(v=>v.currentTime=t);time.textContent=`${fmt(t)} / ${fmt(videos[0].duration||0)}`});
 range.addEventListener('change',()=>dragging=false);buttons.forEach((b,i)=>b.addEventListener('click',()=>loadCase(i)));loadCase(0);
}

setupTeaser();
setupInteractionControls();
setupAnnotationCarousel();
document.querySelectorAll('[data-comparison]').forEach(el=>setupComparison(el.dataset.comparison));
document.querySelector('.copy').addEventListener('click',e=>navigator.clipboard.writeText(document.querySelector('.bibtex').textContent).then(()=>{e.target.textContent='Copied';setTimeout(()=>e.target.textContent='Copy',1200)}));

const publicationLinks=document.querySelector('.publication-links');
const arxivButton=publicationLinks.querySelector('a[href*="arxiv.org/abs"]');
const codePlaceholder=publicationLinks.querySelector('a[href="#BibTeX"]');
codePlaceholder.removeAttribute('href');
codePlaceholder.classList.add('is-static');
codePlaceholder.querySelector('.icon').innerHTML='<i class="fab fa-github"></i>';
codePlaceholder.querySelector('span:last-child').textContent='Code (Coming Soon)';
publicationLinks.insertBefore(codePlaceholder.closest('.link-block'),arxivButton.closest('.link-block'));
