import { expect, test } from 'bun:test';
import React, { act } from '../vendor/backlog-source/node_modules/react';
import { renderToStaticMarkup } from '../vendor/backlog-source/node_modules/react-dom/server';
import { createRoot } from '../vendor/backlog-source/node_modules/react-dom/client';
import { JSDOM } from '../vendor/backlog-source/node_modules/jsdom';
import Board from '../vendor/backlog-source/src/web/components/Board';
import TaskTypeBadge from '../vendor/backlog-source/src/web/components/TaskTypeBadge';

const task = {id:'TASK-9',title:'Synthetic record',status:'Inbox',type:'feature',assignee:[],labels:[],dependencies:[],createdDate:'2026-01-01'};
const boardProps = {tasks:[task],statuses:['Inbox','To Do','In Progress','Review','Blocked','Done'],milestones:[],availableLabels:[],milestoneEntities:[],archivedMilestones:[],isLoading:false,laneMode:'none',onLaneChange:()=>{},onEditTask:()=>{},onNewTask:()=>{},availableTypes:['bug','feature','improvement','investigation','idea'],availablePriorities:['P0','P1','P2','P3'],onFiltersChange:()=>{}};

test('Chinese board renders status columns and native type values without changing user text',()=>{
 const html=renderToStaticMarkup(React.createElement(Board,boardProps));
 const doc=new JSDOM(html).window.document;
 expect([...doc.querySelectorAll('h3')].map(e=>e.textContent)).toEqual(['收件箱','待办','进行中','待验收','受阻','已完成']);
 expect(doc.querySelector('h3 + span.bg-purple-100')).not.toBeNull();
 const option=doc.querySelector('select[aria-label="按类型筛选"] option[value="feature"]');
 expect(option?.textContent).toBe('功能需求');
 expect(doc.body.textContent).toContain('Synthetic record');
 expect(doc.body.textContent).toContain('任务看板');
 expect(doc.body.textContent).not.toContain('All priorities');
});

test('Chinese type badge preserves canonical data and unknown custom types',()=>{
 const known=renderToStaticMarkup(React.createElement(TaskTypeBadge,{type:'feature'}));
 expect(known).toContain('data-task-type="feature"');
 expect(known).toContain('功能需求');
 const custom=renderToStaticMarkup(React.createElement(TaskTypeBadge,{type:'custom-synthetic'}));
 expect(custom).toContain('custom-synthetic');
});

test('selecting a Chinese type option sends canonical value to filter callback',async()=>{
 const dom=new JSDOM('<div id="root"></div>',{url:'http://localhost'});
 globalThis.window=dom.window as any;globalThis.document=dom.window.document;
 globalThis.navigator=dom.window.navigator;globalThis.IS_REACT_ACT_ENVIRONMENT=true;
 let selected:any;
 const root=createRoot(document.getElementById('root')!);
 try{
  await act(async()=>root.render(React.createElement(Board,{...boardProps,onFiltersChange:(value)=>{selected=value;}})));
  const select=document.querySelector('select[aria-label="按类型筛选"]') as HTMLSelectElement;
  await act(async()=>{select.value='feature';select.dispatchEvent(new window.Event('change',{bubbles:true}));});
  expect(selected.taskType).toBe('feature');
 }finally{await act(async()=>root.unmount());dom.window.close();}
});

import TaskDetailsModal from '../vendor/backlog-source/src/web/components/TaskDetailsModal';
import { ThemeProvider } from '../vendor/backlog-source/src/web/contexts/ThemeContext';

test('task detail type selection retains its canonical value while label is Chinese',()=>{
 const dom=new JSDOM('<div></div>',{url:'http://localhost'});
 globalThis.window=dom.window as any;globalThis.document=dom.window.document;globalThis.localStorage=dom.window.localStorage;
 const content=React.createElement(TaskDetailsModal,{task,isOpen:true,onClose:()=>{},availableTypes:['bug','feature'],availableStatuses:boardProps.statuses,availableTasks:[]});
 const html=renderToStaticMarkup(React.createElement(ThemeProvider,null,content));
 const doc=new JSDOM(html).window.document;
 const select=doc.querySelector('select[aria-label="任务类型"]') as HTMLSelectElement;
 expect(select.value).toBe('feature');
 expect(select.selectedOptions[0]?.textContent).toBe('功能需求');
 dom.window.close();
});

test('selected board tasks expose Chinese move labels with canonical status option values',async()=>{
 const dom=new JSDOM('<div id="root"></div>',{url:'http://localhost'});
 globalThis.window=dom.window as any;globalThis.document=dom.window.document;globalThis.navigator=dom.window.navigator;
 const root=createRoot(document.getElementById('root')!);
 try{
  await act(async()=>root.render(React.createElement(Board,boardProps)));
  const card=document.querySelector('[role="button"][draggable="true"]')!;
  await act(async()=>card.dispatchEvent(new window.MouseEvent('click',{bubbles:true,ctrlKey:true})));
  const select=document.querySelector('#batch-move-status') as HTMLSelectElement;
  expect([...select.options].slice(1).map(o=>o.value)).toEqual(boardProps.statuses);
  expect([...select.options].slice(1).map(o=>o.textContent)).toEqual(['收件箱','待办','进行中','待验收','受阻','已完成']);
 }finally{await act(async()=>root.unmount());dom.window.close();}
});
