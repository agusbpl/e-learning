'use strict';
window.ChoiceOrder={
  generate(count){
    const order=Array.from({length:count},(_,i)=>i),sample=new Uint32Array(1);
    for(let i=count-1;i>0;i--){
      const bound=i+1,limit=4294967296-(4294967296%bound);
      do{crypto.getRandomValues(sample);}while(sample[0]>=limit);
      const j=sample[0]%bound;[order[i],order[j]]=[order[j],order[i]];
    }
    return order;
  },
  forAttempt(key,count){
    let saved;try{saved=JSON.parse(GlosaRoom.storage.getItem(key+':order'));}catch{}
    if(!Array.isArray(saved)||saved.length!==count||new Set(saved).size!==count||saved.some(i=>!Number.isInteger(i)||i<0||i>=count)){
      saved=this.generate(count);GlosaRoom.storage.setItem(key+':order',JSON.stringify(saved));
    }
    return saved;
  }
};
