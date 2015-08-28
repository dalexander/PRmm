///////////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2010, Pacific Biosciences of California, Inc.
//
// All rights reserved.
//
// THIS SOFTWARE CONSTITUTES AND EMBODIES PACIFIC BIOSCIENCES' CONFIDENTIAL
// AND PROPRIETARY INFORMATION.
//
// Disclosure, redistribution and use of this software is subject to the
// terms and conditions of the applicable written agreement(s) between you
// and Pacific Biosciences, where "you" refers to you or your company or
// organization, as applicable.  Any other disclosure, redistribution or
// use is prohibited.
//
// THIS SOFTWARE IS PROVIDED BY PACIFIC BIOSCIENCES AND ITS CONTRIBUTORS "AS
// IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
// THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
// PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL PACIFIC BIOSCIENCES OR ITS
// CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
// EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
// PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
// OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
// WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
// OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
// ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//      Description:
//      Fast GBM tree predict routintes
//
//      Patrick Marks (pmarks@pacificbiosciences.com)
//
///////////////////////////////////////////////////////////////////////////////


#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdio.h>
#include <stdint.h>

#define MIN(x, y) (((x) > (y)) ? (y) : (x))

/// <summary>
/// Walk the tree for each example, and sum up the leaf nodes.  Emit the total
/// scores for each observation.
/// </summary>
void innerPredict(float radPredF[], float **dataMatrix, int cRows, int left[], int right[], int missing[], float splitCode[], int splitVar[], int cSplits[], int varTypes[], float initialValue, int treeSize, int numTrees, int maxCSplitSize)
{

    int tStep = 50;
    int obsStep = 60;

    for(int i = 0; i < cRows; i++)
    {
        radPredF[i] = initialValue;
    }

    for (int t0 = 0; t0 < numTrees; t0 += tStep)
    {
        for (int obs0 = 0; obs0 < cRows; obs0 += obsStep)
        {
            for (int t = t0; t < MIN(t0 + tStep, numTrees); t++)
            {
                int offset = t * treeSize;

                for (int iObs = obs0; iObs < MIN(obs0 + obsStep, cRows); iObs++)
                {
                    int iCurrentNode = 0;
                    while (splitVar[offset + iCurrentNode] != -1)
                    {
                        float dX = dataMatrix[splitVar[offset + iCurrentNode]][iObs];
                        // missing?
                        if (isnan(dX))
                        {
                            iCurrentNode = missing[offset + iCurrentNode];
                        }
                        // continuous?
                        else if (varTypes[splitVar[offset + iCurrentNode]] == 0)
                        {
                            if (dX < splitCode[offset + iCurrentNode])
                            {
                                iCurrentNode = left[offset + iCurrentNode];
                            }
                            else
                            {
                                iCurrentNode = right[offset + iCurrentNode];
                            }
                        }
                        else // categorical
                        {
                            int iCatSplitIndicator = cSplits[((int)splitCode[offset + iCurrentNode]*maxCSplitSize) + (int)dX];
                            if (iCatSplitIndicator == -1)
                            {
                                iCurrentNode = left[offset + iCurrentNode];
                            }
                            else if (iCatSplitIndicator == 1)
                            {
                                iCurrentNode = right[offset + iCurrentNode];
                            }
                            else // categorical level not present in training
                            {
                                iCurrentNode = missing[offset + iCurrentNode];
                            }
                        }
                    }
                    radPredF[iObs] += (float)splitCode[offset + iCurrentNode]; // add the prediction
                }
            } // iObs
        } // iTree
    }
}


static uint32_t modToCanonicalMap[8] = { 0, 1, 2, 3, 0, 1, 1, 1 };

/// <summary>
/// Walk the tree for each example, and sum up the leaf nodes.  Emit the total
/// scores for each observation.
/// </summary>
void innerPredictCtx(float radPredF[], uint64_t contextPack[], int cRows, int left[], int right[], int missing[], float splitCode[], int16_t splitVar[], int varTypes[], float initialValue, int treeSize, int numTrees, int maxCSplitSize)
{

    // contextPack contains 24 3-bit numbers in feature order

    uint32_t* uintSplitCode = (uint32_t*) splitCode;

    int tStep = 20;
    int obsStep = 1000;

    for(int i = 0; i < cRows; i++)
    {
        radPredF[i] = initialValue;
    }

    for (int t0 = 0; t0 < numTrees; t0 += tStep)
    {
        for (int obs0 = 0; obs0 < cRows; obs0 += obsStep)
        {
            for (int t = t0; t < MIN(t0 + tStep, numTrees); t++)
            {
                int offset = t * treeSize;

                for (int iObs = obs0; iObs < MIN(obs0 + obsStep, cRows); iObs++)
                {
                    uint64_t ctx = contextPack[iObs];

                    int currentNode = offset;
                    while (splitVar[currentNode] >= 0)
                    {
                        int currentVar = splitVar[currentNode];
                        int ctxPos = currentVar;
                        int isCanonicalFeature = currentVar >= 13;

                        if (isCanonicalFeature)
                            ctxPos = currentVar - 13;

                        // context is packed 4 bits per slot, lower 3 bits are the modified base code
                        uint32_t dX = (ctx >> (4*ctxPos)) & 0x7;

                        if (isCanonicalFeature)
                            // Need the canonical base -- convert
                            // from the general base back to the canonical base
                            dX = modToCanonicalMap[dX];

                        // split code contains packed indicators for each categorical level
                        uint32_t splitPack = uintSplitCode[currentNode];
                        uint32_t ind = (splitPack >> dX) & 0x1;

                        if (ind == 0)
                        {
                            // Left node comes precomputed with offset
                            currentNode = left[currentNode];
                        }
                        else
                        {
                            // Right node come precomputed with offset
                            currentNode = right[currentNode];
                        }
                    }
                    radPredF[iObs] += (float)splitCode[currentNode]; // add the prediction
                }
            } // iObs
        } // iTree
    }
}
