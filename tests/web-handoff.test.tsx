import { expect, test } from 'bun:test';
import React, { act } from '../vendor/backlog-source/node_modules/react';
import { createRoot } from '../vendor/backlog-source/node_modules/react-dom/client';
import { JSDOM } from '../vendor/backlog-source/node_modules/jsdom';
import TaskDetailsModal from '../vendor/backlog-source/src/web/components/TaskDetailsModal';
import { ThemeProvider } from '../vendor/backlog-source/src/web/contexts/ThemeContext';
import { apiClient } from '../vendor/backlog-source/src/web/lib/api';

const task = {id:'TASK-9',title:'Synthetic handoff',status:'To Do',assignee:[],labels:[],dependencies:[],createdDate:'2026-01-01'};

async function detail(run: (button: HTMLButtonElement | undefined) => Promise<void>, overrides = {}, targetText = '复制给 Agent') {
 const dom = new JSDOM('<div id="root"></div>', {url:'http://localhost'});
 Object.assign(globalThis,{window:dom.window,document:dom.window.document,navigator:dom.window.navigator,localStorage:dom.window.localStorage,Element:dom.window.Element,IS_REACT_ACT_ENVIRONMENT:true});
 const root = createRoot(document.getElementById('root')!);
 const statuses = apiClient.fetchStatuses;
 const handoff = apiClient.fetchAgentHandoff;
 apiClient.fetchStatuses = async () => ['Inbox','To Do','In Progress','Blocked','Done'];
 try {
  await act(async () => root.render(React.createElement(ThemeProvider,null,React.createElement(TaskDetailsModal,{task:{...task,...overrides},isOpen:true,onClose:() => {},availableTasks:[]}))));
  await run([...document.querySelectorAll('button')].find(b => b.textContent === targetText));
 } finally {
  await act(async () => root.unmount());
  apiClient.fetchStatuses = statuses;
  apiClient.fetchAgentHandoff = handoff;
  dom.window.close();
 }
}

test('copy button retrieves the selected saved task and copies instructions without updating it', async () => {
 await detail(async button => {
  expect(button).toBeDefined();
  let copied = '';
  Object.defineProperty(navigator,'clipboard',{value:{writeText:async(text:string) => {copied=text;}}});
  apiClient.fetchAgentHandoff = async id => {expect(id).toBe(task.id);return {text:'Synthetic execution instructions'};};
  await act(async () => button!.click());
  expect(copied).toBe('Synthetic execution instructions');
  expect(document.querySelector('[role="status"]')?.textContent).toContain('已复制');
 });
});

test('clipboard denial exposes selectable instructions and never claims success', async () => {
 await detail(async button => {
  Object.defineProperty(navigator,'clipboard',{value:{writeText:async() => {throw new Error('denied');}}});
  apiClient.fetchAgentHandoff = async () => ({text:'Synthetic manual copy'});
  await act(async () => button!.click());
  expect(document.querySelector('[role="status"]')?.textContent).toContain('自动复制失败');
  const textarea = document.querySelector('textarea[aria-label="Agent 执行指令"]') as HTMLTextAreaElement;
  expect(textarea.value).toBe('Synthetic manual copy');
  expect(textarea.readOnly).toBe(true);
 });
});

test('handoff read failure shows the error without reporting a successful copy', async () => {
 await detail(async button => {
  apiClient.fetchAgentHandoff = async () => {throw new Error('无法生成交接指令');};
  await act(async () => button!.click());
  expect(document.querySelector('[role="status"]')?.textContent).toBe('无法生成交接指令');
  expect(document.querySelector('textarea[aria-label="Agent 执行指令"]')).toBeNull();
 });
});

test('drafts, completed archives and other-branch tasks have no execution handoff', async () => {
 for (const overrides of [{status:'Draft'}, {source:'completed'}, {branch:'synthetic-branch'}]) {
  await detail(async button => {expect(button).toBeUndefined();}, overrides);
 }
});

test('deploy checkbox is off by default and passes the authorization only when ticked', async () => {
 await detail(async button => {
  const deploy = document.querySelector('input[aria-label="完成后直接合并部署"]') as HTMLInputElement;
  expect(deploy.checked).toBe(false);
  const calls: unknown[][] = [];
  Object.defineProperty(navigator,'clipboard',{value:{writeText:async() => {}}});
  apiClient.fetchAgentHandoff = async (...args) => {calls.push(args);return {text:'Synthetic instructions'};};
  await act(async () => button!.click());
  await act(async () => deploy.click());
  await act(async () => button!.click());
  expect(calls).toEqual([[task.id,false],[task.id,true]]);
  expect(document.querySelector('[role="status"]')?.textContent).toContain('含完成后合并部署授权');
 });
});

test('research button requests a read-only research handoff', async () => {
 await detail(async button => {
  expect(button).toBeDefined();
  const calls: unknown[][] = [];
  let copied = '';
  Object.defineProperty(navigator,'clipboard',{value:{writeText:async(text:string) => {copied=text;}}});
  apiClient.fetchAgentHandoff = async (...args) => {calls.push(args);return {text:'Synthetic research instructions'};};
  await act(async () => button!.click());
  expect(copied).toBe('Synthetic research instructions');
  expect(calls).toEqual([[task.id,false,'research']]);
  expect(document.querySelector('[role="status"]')?.textContent).toContain('只读调研指令');
 }, {}, '先调研');
});

test('research handoff fallback is labeled separately from execution instructions', async () => {
 await detail(async button => {
  Object.defineProperty(navigator,'clipboard',{value:{writeText:async() => {throw new Error('denied');}}});
  apiClient.fetchAgentHandoff = async () => ({text:'Synthetic manual research'});
  await act(async () => button!.click());
  const textarea = document.querySelector('textarea[aria-label="Agent 调研指令"]') as HTMLTextAreaElement;
  expect(textarea.value).toBe('Synthetic manual research');
 }, {}, '先调研');
});
