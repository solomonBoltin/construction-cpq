
import React from 'react';
import { useStepNavigation } from '../../hooks/useStepNavigation';
import { STEPS } from '../../config/quoteBuilder';
import CheckIcon from '../icons/CheckIcon';

const Stepper: React.FC = () => {
    const { getStepStatus, goToStep } = useStepNavigation();

    return (
        <nav aria-label="Progress" className="p-4 bg-white border-b">
            <ol role="list" className="flex items-center space-x-2 sm:space-x-4 text-xs sm:text-sm font-medium text-slate-500 overflow-x-auto">
                {STEPS.map((step, index) => {
                    const status = getStepStatus(index);
                    const canClick = status !== 'disabled';
                    
                    return (
                        <li key={step.key} className="flex items-center">
                            <button
                                onClick={() => canClick && goToStep(step.key)}
                                disabled={!canClick}
                                className={`
                                    flex items-center gap-2 px-3 py-2 rounded-lg transition-colors
                                    ${status === 'completed' ? 'text-green-600 hover:bg-green-50 cursor-pointer' : ''}
                                    ${status === 'active' ? 'text-blue-600 font-bold bg-blue-50' : ''}
                                    ${status === 'enabled' ? 'text-slate-600 hover:bg-slate-50 cursor-pointer' : ''}
                                    ${status === 'disabled' ? 'text-gray-400 cursor-not-allowed' : ''}
                                `}
                            >
                                <span className={`
                                    flex items-center justify-center w-6 h-6 rounded-full text-xs font-semibold
                                    ${status === 'completed' ? 'bg-green-500 text-white' : ''}
                                    ${status === 'active' ? 'bg-blue-600 text-white' : ''}
                                    ${status === 'enabled' ? 'bg-slate-300 text-slate-700' : ''}
                                    ${status === 'disabled' ? 'bg-gray-200 text-gray-500' : ''}
                                `}>
                                    {status === 'completed' ? <CheckIcon className="w-3 h-3" /> : index + 1}
                                </span>
                                <span className="hidden sm:inline whitespace-nowrap">
                                    {step.label}
                                </span>
                            </button>
                            {index < STEPS.length - 1 && (
                                <div className="hidden sm:block w-8 h-px bg-gray-200 mx-2" />
                            )}
                        </li>
                    );
                })}
            </ol>
        </nav>
    );
};

export default Stepper;
