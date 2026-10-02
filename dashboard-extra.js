// Additions to the existing dashboard, preserving its layout and navigation.
const oldInfo=vInfo, oldSearch=vZoek, oldRender=render;
const oldSpark=spark, oldMin=vMin;
spark=function(m){return Y.some(y=>m.per_jaar[y]===undefined)?'<span class="mut">Niet alle jaren vergelijkbaar</span>':oldSpark(m)};
vMin=function(){const m=D.ministeries.find(x=>x.naam===S.m),html=oldMin();return m&&Y.some(y=>m.per_jaar[y]===undefined)?html.replace(/<svg viewBox[\s\S]*?<\/svg>/,'<p class="mut">Niet alle jaren hebben dit hoofdstuk onder dezelfde naam. Ontbrekende jaren zijn geen nul; de trendgrafiek is daarom weggelaten.</p>'):html};
const orgRows=()=>inY(D.ontvangers).filter(r=>!S.q||`${r.naam} ${r.organisatie||''}`.toLowerCase().includes(S.q.toLowerCase()));
const sourceLink=r=>/^https:\/\/www\.rijksfinancien\.nl\//.test(r.bron)?`<a href="${esc(r.bron)}" target="_blank" rel="noopener">Bron</a>`:'Lokale bron';
function recipientTable(rows){return `<div class="wrap"><table><tr><th>Gepubliceerde ontvanger</th><th>Realisatie</th></tr>${rows.slice(0,200).map(r=>`<tr><td>${esc(r.naam)}${r.organisatie?`<div class="mut">Naamgroep: ${esc(r.organisatie)}</div>`:''}</td><td class="n">${fmt(r.bedrag)}</td></tr>`).join('')}</table></div><p class="mut">${rows.length} resultaten; maximaal 200 getoond. Verfijn de zoekopdracht. Bedragen uit deze bron zijn al euro’s.</p>`}
function vOrgs(){const rows=orgRows().sort((a,b)=>b.bedrag-a.bedrag);
 csv('ontvangers_'+S.y,[['Ontvanger','Naamgroep','Realisatie EUR'],...rows.map(r=>[r.naam,r.organisatie||'',r.bedrag])]);
 return `<div class="card"><h2>Waar stroomt het geld naartoe?</h2><p>${esc(D.organisatie_methode)}</p><p><b>${esc(D.ontvangerdekking[S.y])}</b></p></div>`+
 D.organisaties.map(o=>{const posts=inY(o.begrotingsposten),received=inY(D.ontvangers).filter(r=>r.organisatie===o.organisatie);return `<div class="card"><h2>${esc(o.organisatie)}</h2><h3>Benoemde begrotingsposten · ${esc(D.jaren[S.y].soort)}</h3><div class="wrap"><table>${posts.map(r=>`<tr><td>${esc(r.regeling)}<div class="mut">${esc(r.hoofdstuk)} · ${esc(r.artikel)} · ${esc(r.ibos)} · bronregel ${r.bronregel}</div></td><td class="n">${fmt(r.bedrag)}</td><td>${sourceLink(r)}</td></tr>`).join('')||'<tr><td>Geen exact herkende naam; dit betekent niet dat er geen geldstroom is.</td></tr>'}</table></div><h3>Ontvangersbron · realisaties</h3>${received.length?recipientTable(received):'<p>Geen gekoppelde ontvangergegevens voor dit jaar beschikbaar.</p>'}</div>`}).join('')+
 `<div class="card"><div class="row"><h2>Alle gepubliceerde ontvangers</h2><button class="btn" data-a="csv">Download alle resultaten</button></div>${rows.length?recipientTable(rows):'<p>Geen gegevens beschikbaar.</p>'}</div>`;
}
vReg=function(){const rows=inY(D.grootste_regelingen).sort((a,b)=>b.bedrag-a.bedrag);
 csv('regelingen_'+S.y,[['Regeling','Hoofdstuk','Artikel','IBOS','Bedrag EUR','Bron','Bronregel'],...rows.map(r=>[r.regeling,r.hoofdstuk,r.artikel,r.ibos,r.bedrag,r.bron,r.bronregel])]);
 return `<div class="card"><div class="row"><h2>Regelingen en overige detailposten</h2><button class="btn" data-a="csv">Download alle posten</button></div><p>${rows.length} posten doorzoekbaar; hieronder de 200 grootste. De bron kan onuitgesplitste totalen bevatten. Posten zijn geen extra uitgaven bovenop de artikeltotalen.</p><div class="wrap"><table>${rows.slice(0,200).map(r=>`<tr><td>${esc(r.regeling)}<div class="mut">${esc(r.hoofdstuk)} · ${esc(r.artikel)} · ${esc(r.ibos)}</div></td><td class="n">${fmt(r.bedrag)}</td><td>${sourceLink(r)}</td></tr>`).join('')}</table></div></div>`;
};
vZoek=function(){const rows=orgRows().sort((a,b)=>b.bedrag-a.bedrag);return oldSearch()+`<div class="card"><h2>Ontvangers (${rows.length})</h2><p>${esc(D.ontvangerdekking[S.y])}</p>${rows.length?recipientTable(rows):'<p>Geen ontvanger gevonden in de beschikbare bron; geen bewijs van nul uitgaven.</p>'}</div>`};
vInfo=function(){return oldInfo()+`<div class="card"><h2>Controleerbare bronbestanden</h2><p>Alle bedragen in het dashboard zijn euro’s. De begrotingsbron is vermenigvuldigd met 1.000; de ontvangersbron niet. SHA-256 identificeert de ingelezen bytes.</p>${D.bronnen.map(s=>`<p>${s.jaar} · ${esc(s.type||s.fase)} · ${esc(s.bedragkolom||'EUR')}<br>${sourceLink({bron:s.url})} ${esc(s.archiefbestand||'')}<br><code style="overflow-wrap:anywhere">${esc(s.sha256)}</code></p>`).join('')}</div>`};
function vEU(){const rows=inY(D.bronregels).filter(r=>r.hoofdstukcode==='V'&&r.artikelcode==='3'&&r.totaal==='N'&&r.vuo!=='V');
 const levies=new Set(['BNI-afdrachten','BTW-afdrachten','Invoerrechten','Plastic-grondslag']);
 const total=rows.filter(r=>r.vuo==='U'&&levies.has(r.regeling)).reduce((s,r)=>s+r.bedrag,0);
 csv('eu_buitenlandse_zaken_'+S.y,[['Richting','Post','Bedrag EUR','IBOS','Bron'],...rows.map(r=>[r.vuo,r.regeling,r.bedrag,r.ibos,r.bron])]);
 return `<div class="card"><h2>EU en Europese samenwerking</h2><p>Buitenlandse Zaken, artikel 3. Dit artikel bevat ook andere Europese organisaties, zoals de Raad van Europa en Benelux. Zij zijn geen EU-instellingen.</p><p><b>Herkenbare EU-afdrachten: ${fmt(total)}</b><br>Som van BNI, BTW, plastic-grondslag en invoerrechten aan de uitgavenkant. ${esc(D.jaren[S.y].soort)}; zie de afzonderlijke posten hieronder.</p><p>Ontvangsten staan apart. Deze selectie is geen volledige netto EU-positie van Nederland: directe Europese subsidies aan Nederlandse organisaties en geldstromen via andere begrotingsartikelen ontbreken.</p><button class="btn" data-a="csv">Download deze posten</button></div>`+
 ['U','O'].map(v=>`<div class="card"><h2>${v==='U'?'Uitgaven':'Ontvangsten'} · Europese samenwerking</h2><div class="wrap"><table>${rows.filter(r=>r.vuo===v).map(r=>`<tr><td>${esc(r.regeling)}<div class="mut">${esc(r.ibos)} · bronregel ${r.bronregel}</div></td><td class="n">${fmt(r.bedrag)}</td><td>${sourceLink(r)}</td></tr>`).join('')}</table></div></div>`).join('');
}
TABS.splice(3,0,['organisaties','Organisaties'],['eu','EU']);
render=function(){oldRender();if(S.q.length<2&&!S.m&&S.t==='organisaties')$('#view').innerHTML=vOrgs();
 if(S.q.length<2&&!S.m&&S.t==='eu')$('#view').innerHTML=vEU();
 $('#soort').textContent+=` ${D.controle.length} bronverschillen vastgesteld; zie Signalen & methode. Dekking: Rijk exclusief premies. Ontvangerbedragen niet optellen bij begrotingsbedragen.`;
 if(prevOf(S.y)&&D.jaren[prevOf(S.y)].soort!==D.jaren[S.y].soort)$('#soort').textContent+=' De jaarvergelijking betreft een raming tegenover een realisatie.';
 const note=[...document.querySelectorAll('p.mut')].find(p=>p.textContent==='Alleen de grootste regelingen van het Rijk zijn opgenomen.');
 if(note)note.textContent='Hier de 25 grootste posten van dit hoofdstuk; alle detailposten zijn doorzoekbaar en exporteerbaar via Regelingen.';
};
// Intercept the original export handler: strings beginning with formula markers
// must remain text when opened in a spreadsheet. Numeric values remain numeric.
document.addEventListener('click',e=>{if(!e.target.closest('[data-a="csv"]')||!S.csv)return;e.stopImmediatePropagation();
 const cell=c=>{let v=String(c);if(typeof c==='string'&&/^[\s]*[=+@-]/.test(v))v="'"+v;return '"'+v.replace(/"/g,'""')+'"'};
 const blob=new Blob(['\ufeff'+S.csv.rows.map(r=>r.map(cell).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8'});
 const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=S.csv.name.replace(/\W+/g,'_')+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
},true);
render();
