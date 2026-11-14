import { expect, test } from 'bun:test';
import React, { act } from '../vendor/backlog-source/node_modules/react';
import { createRoot } from '../vendor/backlog-source/node_modules/react-dom/client';
import { JSDOM } from '../vendor/backlog-source/node_modules/jsdom';
import Board from '../vendor/backlog-source/src/web/components/Board';
import { apiClient } from '../vendor/backlog-source/src/web/lib/api';

const tasks = [1,2,3].map(id=>({id:`TASK-${id}`,title:`Synthetic batch ${id}`,status:'To Do',assignee:[],labels:[],dependencies:[],createdDate:'2026-01-01'}));
const props = {tasks,statuses:['Inbox','To Do','In Progress','Blocked','Done'],milestones:[],availableLabels:[],milestoneEntities:[],archivedMilestones:[],isLoading:false,laneMode:'none' as const,onLaneChange:()=>{},onNewTask:()=>{}};

async function board(run: (opened: () => number) => Promise<void>) {
 const dom = new JSDOM('<div id="root"></div>',{url:'http://localhost'});
 Object.assign(globalThis,{window:dom.window,document:dom.window.document,navigator:dom.window.navigator,localStorage:dom.window.localStorage,Element:dom.window.Element,IS_REACT_ACT_ENVIRONMENT:true});
 const root = createRoot(document.getElementById('root')!);
 const original = apiClient.fetchAgentHandoff;
 let opens = 0;
 try {
  await act(async()=>root.render(React.createElement(Board,{...props,onEditTask:()=>{opens++;}})));
  await run(()=>opens);
 } finally {
  await act(async()=>root.unmount());
  apiClient.fetchAgentHandoff = original;
  dom.window.close();
 }
}

const checkbox = (id: number) => document.querySelector(`input[aria-label="选择 TASK-${id}"]`) as HTMLInputElement;
const copyButton = () => [...document.querySelectorAll('button')].find(b=>b.textContent==='复制给 Agent')!;
const researchButton = () => [...document.querySelectorAll('button')].find(b=>b.textContent==='先调研')!;

test('checkbox selection copies exactly the selected IDs without opening task details',async()=>{
 await board(async opened=>{
  let ids: string | string[] = [];
  let copied='';
  apiClient.fetchAgentHandoff = async selected=>{ids=selected;return {text:'Synthetic grouped instructions'};};
  Object.defineProperty(navigator,'clipboard',{value:{writeText:async(text:string)=>{copied=text;}}});
  await act(async()=>{checkbox(1).click();checkbox(3).click();});
  expect(opened()).toBe(0);
  expect(checkbox(1).checked).toBe(true);
  expect(checkbox(2).checked).toBe(false);
  await act(async()=>copyButton().click());
  expect(ids).toEqual(['TASK-1','TASK-3']);
  expect(copied).toBe('Synthetic grouped instructions');
  expect(document.querySelector('[role="status"]')?.textContent).toContain('已复制 2 项');
 });
});

test('changing the selection discards a pending copy of the old task set',async()=>{
 await board(async()=>{
  let resolve!: (value:{text:string})=>void;
  let copied=false;
  apiClient.fetchAgentHandoff = ()=>new Promise(done=>{resolve=done;});
  Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{copied=true;}}});
  await act(async()=>{checkbox(1).click();checkbox(2).click();});
  await act(async()=>copyButton().click());
  await act(async()=>checkbox(2).click());
  await act(async()=>resolve({text:'Stale synthetic batch'}));
  expect(copied).toBe(false);
  expect(document.querySelector('[role="status"]')).toBeNull();
  expect(checkbox(1).checked).toBe(true);
 });
});

test('batch clipboard denial exposes manual copy and clearing selection removes it',async()=>{
 await board(async()=>{
  apiClient.fetchAgentHandoff = async()=>({text:'Synthetic manual batch instructions'});
  Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{throw new Error('denied');}}});
  await act(async()=>{checkbox(1).click();checkbox(2).click();});
  await act(async()=>copyButton().click());
  const manual=document.querySelector('textarea[aria-label="Agent 执行指令"]') as HTMLTextAreaElement;
  expect(manual.value).toBe('Synthetic manual batch instructions');
  expect(document.querySelector('[role="status"]')?.textContent).toContain('自动复制失败');
  const clear=[...document.querySelectorAll('button')].find(b=>b.textContent==='清除')!;
  await act(async()=>clear.click());
  expect(document.querySelector('textarea[aria-label="Agent 执行指令"]')).toBeNull();
  expect(document.querySelector('[aria-label="任务选择"]')).toBeNull();
 });
});

test('batch deploy checkbox applies to the current selection only',async()=>{
 await board(async()=>{
  const calls: unknown[][] = [];
  apiClient.fetchAgentHandoff = async(...args)=>{calls.push(args);return {text:'Synthetic batch'};};
  Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{}}});
  const deploy=()=>document.querySelector('input[aria-label="完成后直接合并部署"]') as HTMLInputElement;
  await act(async()=>{checkbox(1).click();checkbox(2).click();});
  await act(async()=>deploy().click());
  await act(async()=>copyButton().click());
  expect(calls).toEqual([[['TASK-1','TASK-2'],true]]);
  await act(async()=>checkbox(3).click());
  expect(deploy().checked).toBe(false);
 });
});

test('batch research button requests read-only research instructions',async()=>{
 await board(async()=>{
  const calls: unknown[][] = [];
  let copied='';
  apiClient.fetchAgentHandoff = async(...args)=>{calls.push(args);return {text:'Synthetic batch research'};};
  Object.defineProperty(navigator,'clipboard',{value:{writeText:async(text:string)=>{copied=text;}}});
  await act(async()=>{checkbox(1).click();checkbox(2).click();});
  await act(async()=>researchButton().click());
  expect(calls).toEqual([[['TASK-1','TASK-2'],false,'research']]);
  expect(copied).toBe('Synthetic batch research');
  expect(document.querySelector('[role="status"]')?.textContent).toContain('只读调研指令');
 });
});
